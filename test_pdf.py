import re
from pprint import pprint

from fitz import Document

from remarks.output.ObsidianMarkdownFile import merge_highlights
from remarks.output.PdfFile import extract_annot
from tests.notebook_fixtures import *
from tests.pdf_test_support import assert_page_renders_without_warnings, assert_warning_exists

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
        if page_metadata.raw_highlights:
            if scrybble_warning_typed_text_highlighting_not_supported in page_metadata.warnings:
                continue
            document_page = remarks_document[page_metadata.pdf_document_index]
            words_on_page = document_page.get_textpage().extractWORDS()
            annots = list(document_page.annots())

            # sort by reading-order
            annots.sort(key=lambda a: (a.rect.y0, a.rect.x0))
            assert len(annots) == len(page_metadata.raw_highlights)
            for i, annotation in enumerate(annots):
                text = extract_annot(annotation, words_on_page)
                assert text == page_metadata.raw_highlights[i]
                # TODO: We should implement the colour check as well, once that is ready.


def demarkdown(markdown_text: str):
    """Takes in a Markdown string, and gets rid of all Markdown, essentially returning pure plaintext"""

    # Process the Markdown text to remove formatting
    text = markdown_text

    # Remove headers (# Header)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic formatting
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # Bold
    text = re.sub(r'([*_])(.*?)\1', r'\2', text)  # Italic

    # Remove code blocks and inline code
    text = re.sub(r'```[\s\S]*?```', '', text)  # Code blocks
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code

    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove links - [text](url) -> text
    text = re.sub(r'\[([^]]+)]\([^)]+\)', r'\1', text)

    # Remove image syntax - ![alt](url) -> alt
    text = re.sub(r'!\[([^]]+)]\([^)]+\)', r'\1', text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove ordered/unordered list markers
    text = re.sub(r'^\s*[*\-+]\s+', '', text, flags=re.MULTILINE)  # Unordered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # Ordered lists

    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text



@pytest.mark.pdf
@pytest.mark.unfinished_feature
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_typed_text_is_readable(notebook: NotebookMetadata, remarks_document: Document):
    pages_with_typed_text = list(filter(lambda x: x.typed_text is not None, notebook.pages))

    if pages_with_typed_text:
        for page in pages_with_typed_text:
            document_page = remarks_document[page.pdf_document_index]
            plaintext = demarkdown(page.typed_text)
            for line in document_page.get_textpage().extractText().splitlines():
                assert line in plaintext
