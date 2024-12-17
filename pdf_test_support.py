from fitz import fitz, Document, PDF_ANNOT_FREE_TEXT


def is_valid_pdf(document: Document) -> bool:
    return document.is_pdf

def pdf_has_num_pages(document: Document, num_pages: int) -> bool:
    return document.page_count == num_pages


def assert_scrybble_warning_appears_on_page(document: Document, page_number: int):
    """
    @param document:
    @param page_number: 0-indexed page number
    @return:
    """
    page = document[page_number]
    for annotation in page.annots(PDF_ANNOT_FREE_TEXT):
        print(annotation.get_text())
        if "Scrybble error" in annotation.get_text():
            assert True
            return

    assert False, f"No Scrybble warning found on page {page_number}"
