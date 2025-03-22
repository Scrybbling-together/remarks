import logging
import os
import pathlib
import sys
import tempfile
import zipfile

import fitz  # PyMuPDF
from rmc.exporters.pdf import svg_to_pdf
from rmc.exporters.svg import build_anchor_pos, get_bounding_box
from rmc.exporters.svg import rm_to_svg, xx, yy

from .Document import Document
from .conversion.parsing import (
    parse_rm_file,
    read_rm_file_version, )
from .metadata import ReMarkableAnnotationsFileHeaderVersion
from .output.ObsidianMarkdownFile import ObsidianMarkdownFile
from .output.PdfFile import apply_smart_highlights, add_error_annotation
from .utils import (
    is_document,
    get_document_filetype,
    get_visible_name,
    get_ui_path,
)
from .warnings import scrybble_warning_only_v6_supported


def run_remarks(
        input_dir, output_dir
):
    if input_dir.endswith(".rmn"):
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(input_dir, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        input_dir = temp_dir

    num_docs = sum(1 for _ in pathlib.Path(f"{input_dir}/").glob("*.metadata"))

    if num_docs == 0:
        logging.warning(
            f'No .metadata files found in "{input_dir}". Are you sure you\'re running remarks on a valid xochitl-like directory? See: https://github.com/lucasrla/remarks#1-copy-remarkables-raw-document-files-to-your-computer'
        )
        sys.exit(1)

    logging.info(
        f'\nFound {num_docs} documents in "{input_dir}", will process them now',
    )

    for metadata_path in pathlib.Path(f"{input_dir}/").glob("*.metadata"):
        if not is_document(metadata_path):
            continue

        doc_type = get_document_filetype(metadata_path)
        # Both "Quick Sheets" and "Notebooks" have doc_type="notebook"
        supported_types = ["pdf", "epub", "notebook"]

        doc_name = get_visible_name(metadata_path)

        if not doc_name:
            continue

        if doc_type in supported_types:
            logging.info(f'\nFile: "{doc_name}.{doc_type}" ({metadata_path.stem})')

            in_device_dir = get_ui_path(metadata_path)
            out_path = pathlib.Path(f"{output_dir}/{in_device_dir}/{doc_name}/")

            process_document(metadata_path, out_path)
        else:
            logging.info(
                f'\nFile skipped: "{doc_name}" ({metadata_path.stem}) due to unsupported filetype: {doc_type}. remarks only supports: {", ".join(supported_types)}'
            )

    logging.info(
        f'\nDone processing "{input_dir}"',
    )


def process_document(
        metadata_path,
        out_path,
):
    document = Document(metadata_path)
    rmc_pdf_src = document.open_source_pdf()

    obsidian_markdown = ObsidianMarkdownFile(document)
    obsidian_markdown.add_document_header()

    for (
            page_uuid,
            page_idx,
            rm_annotation_file,
            has_annotations,
            rm_highlights_file,
    ) in document.pages():
        print(f"processing page {page_idx}, {page_uuid}")
        page = rmc_pdf_src[page_idx]
        rm_file_version = read_rm_file_version(rm_annotation_file)

        if rm_file_version == ReMarkableAnnotationsFileHeaderVersion.V6:
            (ann_data, has_ann_hl), version = parse_rm_file(rm_annotation_file)
            temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", mode="w", delete=False)
            temp_svg = tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False)
            try:
                # convert the pdf
                rm_to_svg(rm_annotation_file, temp_svg.name)
                with open(temp_svg.name, "r") as svg_f, open(temp_pdf.name, "wb") as pdf_f:
                    svg_to_pdf(svg_f, pdf_f)
                svg_pdf = fitz.open(temp_pdf.name)

                # This offset is used for smart highlights
                highlights_x_translation = 0

                # if the background page is not empty, need to merge svg on top of background page
                if page.get_contents():
                    w_bg, h_bg = page.cropbox.width, page.cropbox.height
                    # find the (top, right) coordinates of the svg
                    anchor_pos = build_anchor_pos(ann_data["scene_tree"].root_text)
                    x_min, x_max, y_min, y_max = get_bounding_box(ann_data["scene_tree"].root, anchor_pos)
                    x_shift, y_shift, w_svg, h_svg = xx(x_min), yy(y_min), xx(x_max - x_min + 1), yy(y_max - y_min + 1)

                    # compute the width/height of a blank page that can contain both svg and background pdf
                    width, height = max(w_svg, w_bg), max(h_svg, h_bg)
                    # compute position of svg and background in the new_page
                    # it aligns the top-middle of the background and with the (0, 0) of the svg
                    x_svg, y_svg = 0, 0
                    x_bg, y_bg = 0, 0

                    if w_svg > w_bg:
                        x_bg = width / 2 - w_bg / 2 - (w_svg / 2 + x_shift)
                        highlights_x_translation = x_bg
                    elif w_svg < w_bg:
                        x_svg = width / 2 - w_svg / 2 + (w_svg / 2 + x_shift)
                        highlights_x_translation = x_svg
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
                                        page_idx)
                    page.show_pdf_page(fitz.Rect(x_svg, y_svg, x_svg + w_svg, y_svg + h_svg),
                                        svg_pdf,
                                        0)

                    if ann_data and "highlights" in ann_data:
                        apply_smart_highlights(page, ann_data["highlights"], highlights_x_translation)
                    rmc_pdf_src.insert_pdf(doc, start_at=page_idx)
                else:
                    rmc_pdf_src.insert_pdf(svg_pdf, start_at=page_idx)
                rmc_pdf_src.delete_page(page_idx + 1)
            except AttributeError:
                add_error_annotation(page)
            finally:
                temp_pdf.close()
                os.remove(temp_pdf.name)
                temp_svg.close()
                os.remove(temp_svg.name)
            if ann_data:
                if "text" in ann_data:
                    obsidian_markdown.add_text(page_idx, ann_data['text'])
                if "glyph_ranges" in ann_data:
                    obsidian_markdown.add_highlights(page_idx, ann_data["glyph_ranges"])
        else:
            scrybble_warning_only_v6_supported.render_as_annotation(page)

    out_doc_path_str = f"{out_path.parent}/{out_path.name}"
    rmc_pdf_src.save(f"{out_doc_path_str} _remarks.pdf")
    obsidian_markdown.save(out_doc_path_str)


