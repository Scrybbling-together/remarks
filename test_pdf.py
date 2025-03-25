import pytest
from fitz import Document

from tests.pdf_test_support import assert_page_renders_without_warnings, assert_warning_exists
from remarks.output.PdfFile import extract_annot
from tests.notebook_fixtures import *


r"""
 _____  _____  ______
|  __ \|  __ \|  ____|
| |__) | |  | | |__
|  ___/| |  | |  __|
| |    | |__| | |
|_|    |_____/|_|
"""
@pytest.mark.pdf
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_valid_pdf(notebook: NotebookMetadata, remarks_document: Document):
    assert remarks_document.is_pdf


@pytest.mark.pdf
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_correct_output_page_count(notebook: NotebookMetadata, remarks_document: Document):
    assert remarks_document.page_count == notebook.pdf_pages


@pytest.mark.pdf
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_warnings_match_specification(notebook: NotebookMetadata, remarks_document: Document):
    for page in notebook.pages:
        print(page.warnings)
        if page.warnings:
            for warning in page.warnings:
                assert_warning_exists(remarks_document, page.pdf_document_index, warning)
        else:
            # If no warnings specified for this page, verify page is clean
            assert_page_renders_without_warnings(remarks_document, page.pdf_document_index)


@pytest.mark.pdf
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_smart_highlights(notebook: NotebookMetadata, remarks_document: Document):
    for page_metadata in notebook.pages:
        if page_metadata.smart_highlights:
            if scrybble_warning_typed_text_highlighting_not_supported in page_metadata.warnings:
                continue
            document_page = remarks_document[page_metadata.pdf_document_index]
            words_on_page = document_page.get_textpage().extractWORDS()
            annots = list(document_page.annots())

            # sort by reading-order
            annots.sort(key=lambda a: (a.rect.y0, a.rect.x0))
            assert len(annots) == len(page_metadata.smart_highlights)
            for i, annotation in enumerate(annots):
                text = extract_annot(annotation, words_on_page)
                assert text == page_metadata.smart_highlights[i]
                # TODO: We should implement the colour check as well, once that is ready.