from fitz import fitz, Document

def is_valid_pdf(document: Document) -> bool:
    return document.is_pdf

def pdf_has_num_pages(document: Document, num_pages: int) -> bool:
    return document.page_count == num_pages

