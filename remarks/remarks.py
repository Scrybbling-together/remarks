import logging
import os
import pathlib
import sys
import tempfile
import zipfile

import fitz  # PyMuPDF
from rmc.exporters.pdf import rm_to_pdf
from rmc.exporters.svg import build_anchor_pos, get_bounding_box, set_device_from_pdf_size, set_device
from rmc.exporters.svg import rm_to_svg, xx, yy

import rmc

from .Document import Document
from .conversion.parsing import (
    parse_rm_file,
    read_rm_file_version, )
from .metadata import ReMarkableAnnotationsFileHeaderVersion
from .output.ObsidianMarkdownFile import ObsidianMarkdownFile
from .output.PdfFile import apply_smart_highlight, add_error_annotation
from .utils import (
    is_document,
    get_document_filetype,
    get_visible_name,
    get_ui_path,
)
from .warnings import scrybble_warning_only_v6_supported



def run_remarks(
        input_dir: pathlib.Path, output_dir: pathlib.Path,
        device: str = None
):
    if input_dir.name.endswith(".rmn") or input_dir.name.endswith(".rmdoc"):
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(input_dir, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        input_dir = pathlib.Path(temp_dir)

    num_docs = sum(1 for _ in input_dir.glob("*.metadata"))

    if num_docs == 0:
        logging.warning(
            f'No .metadata files found in "{input_dir}". Are you sure you\'re running remarks on a valid xochitl-like directory? See: https://github.com/lucasrla/remarks#1-copy-remarkables-raw-document-files-to-your-computer'
        )
        sys.exit(1)

    logging.info(
        f'\nFound {num_docs} documents in "{input_dir}", will process them now',
    )

    for metadata_path in input_dir.glob("*.metadata"):
        if not is_document(metadata_path):
            continue

        doc_type = get_document_filetype(metadata_path)
        # Both "Quick Sheets" and "Notebooks" have doc_type="notebook"
        supported_types = ["pdf", "epub", "notebook"]

        doc_name = get_visible_name(metadata_path)

        if not doc_name:
            continue

        if doc_type in supported_types:
            logging.info(f'\nFile: "{doc_name} [type={doc_type}]" ({metadata_path.stem})')

            in_device_dir = get_ui_path(metadata_path)
            relative_doc_path = pathlib.Path(f"{in_device_dir}/{doc_name}")

            process_document(metadata_path, relative_doc_path, output_dir,
                             device=device)
        else:
            logging.info(
                f'\nFile skipped: "{doc_name}" ({metadata_path.stem}) due to unsupported filetype: {doc_type}. remarks only supports: {", ".join(supported_types)}'
            )

    logging.info(
        f'\nDone processing "{input_dir}"',
    )


def process_document(
        metadata_path: pathlib.Path,
        relative_doc_path: pathlib.Path,
        output_dir: pathlib.Path,
        device: str = None
):

    document = Document(metadata_path)
    rmc_pdf_src = document.open_source_pdf()

    obsidian_markdown = ObsidianMarkdownFile(document)

    # First, add page tags for ALL pages (including those without .rm files)
    for page_idx, page_uuid in enumerate(document.pages_list):
        page_tags = document.get_page_tags_for_page(page_uuid)
        if page_tags:
            obsidian_markdown.add_page_tags(page_idx, page_tags)

    for (
            page_uuid,
            page_idx,
            rm_annotation_file,
    ) in document.pages():
        logging.info(f"processing page {page_idx + 1}, {page_uuid}")
        page = rmc_pdf_src[page_idx]

        rm_file_version = read_rm_file_version(rm_annotation_file)

        if rm_file_version == ReMarkableAnnotationsFileHeaderVersion.V6:
            (ann_data, has_ann_hl), version = parse_rm_file(rm_annotation_file)
            temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", mode="w", delete=False)

            # This offset is used for smart highlights
            highlights_x_translation = 0
            try:
                # Detect device type from PDF page dimensions and configure SVG exporter
                page_rotation = page.rotation
                page.set_rotation(0)
                w_bg, h_bg = page.cropbox.width, page.cropbox.height
                if int(page_rotation) in [90, 270]:
                    w_bg, h_bg = h_bg, w_bg
                page.set_rotation(page_rotation)  # Restore rotation
                if device:
                    set_device(device)
                else:
                    set_device_from_pdf_size(w_bg, h_bg)

                # convert the pdf
                rm_to_pdf(rm_annotation_file, temp_pdf.name)

                svg_pdf = fitz.open(temp_pdf.name)

                # if the background page is not empty, need to merge svg on top of background page
                if page.get_contents():
                    # w_bg, h_bg already calculated above for device detection
                    # find the (top, right) coordinates of the svg
                    anchor_pos = build_anchor_pos(ann_data["scene_tree"].root_text)
                    x_min, x_max, y_min, y_max = get_bounding_box(ann_data["scene_tree"].root, anchor_pos)
                    x_shift, y_shift, w_svg, h_svg = xx(x_min), yy(y_min), xx(x_max - x_min + 1), yy(y_max - y_min + 1)

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
                                        page_idx,
                                       rotate=-page_rotation)
                    page.show_pdf_page(fitz.Rect(x_svg, y_svg, x_svg + w_svg, y_svg + h_svg),
                                        svg_pdf,
                                        0)

                    rmc_pdf_src.insert_pdf(doc, start_at=page_idx)
                else:
                    rmc_pdf_src.insert_pdf(svg_pdf, start_at=page_idx)
                rmc_pdf_src.delete_page(page_idx + 1)
            except AttributeError:
                add_error_annotation(page)
            finally:
                temp_pdf.close()
                os.remove(temp_pdf.name)

            if ann_data:
                if "text" in ann_data:
                    obsidian_markdown.add_text(page_idx, ann_data['text'])
                if "glyph_ranges" in ann_data:
                    obsidian_markdown.add_highlights(page_idx, ann_data["glyph_ranges"])
                if ann_data["highlights"]:
                    for highlight in ann_data["highlights"]:
                        apply_smart_highlight(rmc_pdf_src[page_idx], highlight, highlights_x_translation)
        else:
            scrybble_warning_only_v6_supported.render_as_annotation(page)

    output_pdf_path = output_dir/f"{relative_doc_path} _remarks.pdf"
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    rmc_pdf_src.save(output_pdf_path)

    output_obsidian_path = output_dir/f"{relative_doc_path}"
    obsidian_markdown.save(output_obsidian_path)
