from enum import Enum


class ReMarkableNotebookType(Enum):
    """The ReMarkable notebook Enum describes how the document was first created on the ReMarkable tablet."""

    NOTEBOOK = "Notebook"
    """A notebook is a ReMarkable notebook or a quicksheets document"""
    EBOOK = "EBook"
    """An ebook is a .epub (electronic publication) file"""
    PDF = "PDF"
    """A PDF is a .pdf (postscript document format) file"""
