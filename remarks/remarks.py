import logging
import os
import pathlib
import sys
import tempfile
import zipfile
from traceback import format_exc
from typing import List

import fitz  # PyMuPDF
from pylibrm_lines import SceneTree, FailedToBuildTree
from rm_api.models import LocalDocument
from rmc.exporters.pdf import rm_to_pdf
import rmc.exporters.svg as svg_exporter
from rmc.exporters.svg import build_anchor_pos, get_bounding_box, set_device, set_dimensions_for_pdf, rmc_config
from rmc.exporters.svg import rm_to_svg

import rmc

from .Document import Document
from .conversion.parsing import (
    parse_rm_file,
    read_rm_file_version, )
from .metadata import ReMarkableAnnotationsFileHeaderVersion
from .output.ObsidianMarkdownFile import ObsidianMarkdownFile
from .output.PdfFile import apply_smart_highlight, add_error_annotation
from .processor import DocumentProcessor
from .utils import (
    is_document,
    get_document_filetype,
    get_visible_name,
    get_ui_path,
    get_writable_tempdir,
)
from .warnings import scrybble_warning_tree_failed_to_build

REMARKS_TEMP_DIR = get_writable_tempdir()


def run_remarks(
        input_dir: pathlib.Path, output_dir: pathlib.Path,
        device: str = None
):
    docs: List[LocalDocument] = []
    paths: List[pathlib.Path] = []
    if not os.path.isdir(input_dir):
        docs.append(LocalDocument.load_rmdoc(input_dir))
        paths.append(input_dir)

        logging.info(
            f'\nProcessing just one doc "{input_dir}"',
        )
    else:
        for file in os.listdir(input_dir):
            try:
                docs.append(LocalDocument.load_rmdoc(input_dir / file))
            except (zipfile.BadZipFile, FileNotFoundError):
                logging.warning(f"Skipping {file} as it is not a valid reMarkable document")
            paths.append(input_dir / file)

        logging.info(
            f'\nFound {len(docs)} documents in "{input_dir}", will process them now',
        )

    for doc, path in zip(docs, paths):
        logging.info(f'\nFile: "{doc.metadata.visible_name} [type={doc.metadata.type}]" ({path})')
        processor = DocumentProcessor(doc, output_dir)
        try:
            processor.run()
        except:
            logging.error(f"Error processing document {doc.metadata.visible_name}:\n{format_exc()}")
            continue

    logging.info(
        f'\nDone processing "{input_dir}"',
    )


def process_document(document: LocalDocument, output_dir: pathlib.Path):
    # rmc_pdf_src = document.open_source_pdf()


    for i, page in enumerate(document.content.c_pages.pages):

        # Set SVG dimensions: use PDF dimensions if there's backing content,
        # otherwise use device setting for notebooks
        has_backing_pdf = page.get_contents()
        if has_backing_pdf:
            logging.info(f"Setting page dimensions based on pdf: {round(w_bg, 2)} x {round(h_bg, 2)}")
            set_dimensions_for_pdf(w_bg, h_bg)
        elif device:
            logging.info(f"Setting page dimensions based on device: {device}")
            set_device(device)
        else:
            logging.warning(
                f"Unknown device and no backing pdf: setting page size to RMPP (if this is incorrect, specify device with --device)")
            set_device('RMPP')

        (ann_data, has_ann_hl), version = parse_rm_file(rm_annotation_file)
        temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", mode="w", delete=False, dir=REMARKS_TEMP_DIR)

        # This offset is used for smart highlights
        highlights_x_translation = 0
        try:

            # convert the pdf
            rm_to_pdf(rm_annotation_file, temp_pdf.name)

            svg_pdf = fitz.open(temp_pdf.name)

            # if the background page is not empty, need to merge svg on top of background page
            if has_backing_pdf:
                # w_bg, h_bg already calculated above
                # find the (top, right) coordinates of the svg
                anchor_pos = build_anchor_pos(ann_data["scene_tree"].root_text)
                # Convert PDF dimensions to screen coordinates for bounding box default
                # PDF uses points (72 DPI), screen uses device DPI; SCALE = 72/DPI
                # reMarkable uses center-top origin: x from -w/2 to w/2, y from 0 to h
                w_bg_screen = w_bg / rmc_config.scale
                h_bg_screen = h_bg / rmc_config.scale
                pdf_default_bounds = (-w_bg_screen / 2, w_bg_screen / 2, 0, h_bg_screen)
                x_min, x_max, y_min, y_max = get_bounding_box(
                    ann_data["scene_tree"].root, anchor_pos, default=pdf_default_bounds
                )
                x_shift, y_shift, w_svg, h_svg = rmc_config.xx(x_min), rmc_config.yy(y_min), rmc_config.xx(
                    x_max - x_min + 1), rmc_config.yy(y_max - y_min + 1)

                # compute the width/height of a blank page that can contain both svg and background pdf
                width, height = max(w_svg, w_bg), max(h_svg, h_bg)
                # compute position of svg and background in the new_page
                # reMarkable (0,0) is at center-top of PDF page
                # SVG coordinates need to be positioned relative to this center-top origin
                x_svg, y_svg = 0, 0
                x_bg, y_bg = 0, 0

                if w_svg > w_bg:
                    x_bg = width / 2 - w_bg / 2 - (w_svg / 2 + x_shift)
                    # Highlights need to account for reMarkable's center-top origin: PDF center = w_bg/2
                    highlights_x_translation = x_bg + w_bg / 2
                elif w_svg < w_bg:
                    x_svg = width / 2 - w_svg / 2 + (w_svg / 2 + x_shift)
                    # When SVG is smaller, PDF spans full width, so center is at w_bg/2
                    highlights_x_translation = w_bg / 2
                if h_svg > h_bg:
                    y_bg = - y_shift
                elif h_svg < h_bg:
                    y_svg = y_shift

                # create the merged page in independent document as show_pdf_page can't be done on the same document
                doc = fitz.open()
                page = doc.new_page(-1,
                                    width=width,
                                    height=height)
                page.show_pdf_page(fitz.Rect(x_bg, y_bg, x_bg + w_bg, y_bg + h_bg),
                                   rmc_pdf_src,
                                   i,
                                   rotate=-page_rotation)
                page.show_pdf_page(fitz.Rect(x_svg, y_svg, x_svg + w_svg, y_svg + h_svg),
                                   svg_pdf,
                                   0)

                rmc_pdf_src.insert_pdf(doc, start_at=i)
            else:
                rmc_pdf_src.insert_pdf(svg_pdf, start_at=i)
            rmc_pdf_src.delete_page(i + 1)
        except AttributeError:
            add_error_annotation(page)
        finally:
            temp_pdf.close()
            os.remove(temp_pdf.name)

        if ann_data:
            if "text" in ann_data:
                obsidian_markdown.add_text(i, ann_data['text'])
            if "glyph_ranges" in ann_data:
                obsidian_markdown.add_highlights(i, ann_data["glyph_ranges"])
            if ann_data["highlights"]:
                for highlight in ann_data["highlights"]:
                    apply_smart_highlight(rmc_pdf_src[i], highlight, highlights_x_translation)

    output_pdf_path = output_dir / f"{relative_doc_path} _remarks.pdf"
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    rmc_pdf_src.save(output_pdf_path)

    output_obsidian_path = output_dir / f"{relative_doc_path}"
    obsidian_markdown.save(output_obsidian_path)
