import logging
import os
import pathlib
import sys
import tempfile
import zipfile

import fitz  # PyMuPDF
from fitz import Page
from rmc.exporters.pdf import rm_to_pdf

from .Document import Document
from .conversion.parsing import (
    parse_rm_file,
    read_rm_file_version,
)
from .conversion.text import (
    extract_groups_from_smart_hl,
)
from .metadata import ReMarkableAnnotationsFileHeaderVersion
from .output.ObsidianMarkdownFile import ObsidianMarkdownFile
from .utils import (
    is_document,
    get_document_filetype,
    get_visible_name,
    get_ui_path,
    load_json_file,
)


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
        has_smart_highlights,
    ) in document.pages():
        print(f"processing page {page_idx}, {page_uuid}")
        page = rmc_pdf_src[page_idx]
        rm_file_version = read_rm_file_version(rm_annotation_file)

        if rm_file_version == ReMarkableAnnotationsFileHeaderVersion.V6:
            temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", mode="w", delete=False)
            try:
                rm_to_pdf(rm_annotation_file, temp_pdf.name)
                temp_pdf.close()
                p = fitz.open(temp_pdf.name)
                # dumb workaround
                if len(page.read_contents()) < 5:
                    rmc_pdf_src.delete_page(page_idx)
                rmc_pdf_src.insert_pdf(p, start_at=page_idx)
            except AttributeError:
                add_error_annotation(page)
            finally:
                os.remove(temp_pdf.name)
        else:
            add_error_annotation(page)

        (ann_data, has_ann_hl), version = parse_rm_file(rm_annotation_file)

        if ann_data:
            if "text" in ann_data:
                obsidian_markdown.add_text(page_idx, ann_data['text'])
            if "highlights" in ann_data:
                obsidian_markdown.add_highlights(page_idx, ann_data["highlights"])

        if has_smart_highlights:
            smart_hl_data = load_json_file(rm_highlights_file)
            extract_groups_from_smart_hl(smart_hl_data)

    out_doc_path_str = f"{out_path.parent}/{out_path.name}"

    rmc_pdf_src.save(f"{out_doc_path_str} _remarks.pdf")

    obsidian_markdown.save(out_doc_path_str)


def add_error_annotation(page: Page):
    page.add_freetext_annot(
        rect=fitz.Rect(10, 10, 300, 30),
        text="Scrybble error",
        fontsize=11,
        text_color=(0, 0, 0),
        fill_color=(1, 1, 1)
    )

