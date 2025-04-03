from dataclasses import dataclass, field
from typing import Optional, List, Dict

from RemarkableNotebookType import ReMarkableNotebookType

from remarks.metadata import ReMarkableAnnotationsFileHeaderVersion, ReMarkableDevice
from remarks.warnings import ScrybbleWarning


@dataclass
class PageMetadata:
    """A single page in a ReMarkable notebook"""
    rm_file_version: ReMarkableAnnotationsFileHeaderVersion
    """The .rm file version"""

    pdf_document_index: int
    """What page number this .rm page has in a rendered PDF.
    Note, page numbers are 0-indexed, even though PDFs are 1-indexed when read with a reader program."""

    smart_highlights: Optional[List[str]] = None
    """a list of expected highlights. Each highlight is a string of text."""

    typed_text: Optional[str] = None
    """Text written with the Type Folio or with the text tool. Formatted as the equivalent markdown.
    Note that headers are rendered as h5 (#####), and medium text is rendered as h6 (######)"""

    tags: Optional[List[str]] = None
    """A list of tags associated with the page"""

    warnings: List[ScrybbleWarning] = field(default_factory=list)
    """Warnings related to the page."""

    photo: Optional[Dict[ReMarkableDevice, str]] = None
    """A photograph of the page as rendered on a real ReMarkable device"""



@dataclass
class NotebookMetadata:
    """Notebook metadata is meant to describe the inputs and the outputs for a test scenario"""

    notebook_name: str
    """The name of the notebook, as rendered on the ReMarkable tablet software itself"""

    pages: List[PageMetadata]
    """A list of .rm files with associated metadata"""

    rmn_source: str
    """Where the ReMarkable notebook file (.rmn) can be found."""

    description: str
    """A description of the notebook"""

    notebook_type: ReMarkableNotebookType
    """What 'kind of' notebook this is, is it a PDF? Quick sheets? Epub?"""

    pdf_pages: int
    """How many pages the PDF has in total when viewed on a ReMarkable tablet."""

    def get_page_by_pdf_page_number(self, pdf_page_number: int) -> Optional[PageMetadata]:
        """
        Retrieve a PageMetadata object by its pdf_document_index.

        Args:
            pdf_page_number: The pdf_document_index to search for

        Returns:
            The matching PageMetadata object or None if not found
        """
        for page in self.pages:
            if page.pdf_document_index == pdf_page_number:
                return page
        return None