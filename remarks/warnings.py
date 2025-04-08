from dataclasses import dataclass

from fitz.fitz import Page, PDF_ANNOT_TEXT


@dataclass
class ScrybbleWarning:
    message: str

    def __str__(self):
        return f"Scrybble warning: {self.message}"

    def render_as_annotation(self, pdf_page: Page):
        pdf_page.add_text_annot(
            point=(10, 10),
            text=str(self),
            icon="Note"
        )

    def exists_in_pdf_annotation(self, annotation: PDF_ANNOT_TEXT) -> bool:
        return str(self) in annotation.get_text()


scrybble_warning_only_v6_supported = ScrybbleWarning("This page is not V6")

scrybble_warning_typed_text_highlighting_not_supported = ScrybbleWarning("Highlights on typed text is currently not supported")