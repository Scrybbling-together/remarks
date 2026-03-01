"""Test that orphaned .rm files (from deleted pages) don't crash processing."""
import pytest
from conftest import with_remarks
from tests.notebook_fixtures import *


@pytest.mark.pdf
def test_orphaned_rm_file_does_not_crash(orphaned_rm_file_document):
    """Processing a document with an .rm file not listed in .content should not crash."""
    remarks_document = with_remarks(orphaned_rm_file_document)
    assert remarks_document.is_pdf
    assert remarks_document.page_count == orphaned_rm_file_document.pdf_pages
