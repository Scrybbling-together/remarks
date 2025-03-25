import glob
import os
from dataclasses import dataclass

import pytest
import fitz
import shutil
from fitz import Document

import remarks
from tests.NotebookMetadata import NotebookMetadata

def cleanup_output_folder():
    """Remove all .md and .pdf files from the tests/out folder."""
    for file_pattern in ['tests/out/*.md', 'tests/out/*.pdf']:
        for file in glob.glob(file_pattern):
            os.remove(file)

def pytest_sessionstart(session):
    cleanup_output_folder()


def pytest_addoption(parser):
    parser.addoption(
        "--interactive",
        action="store_true",
        default=False,
        help="run interactive tests that require developer verification"
    )


def with_remarks(metadata: NotebookMetadata):
    input_name = metadata.rmn_source

    input_dir = input_name
    output_dir = "tests/out"

    if not getattr(with_remarks, f"run_{input_name}", False):
        remarks.run_remarks(input_dir, output_dir)
        setattr(with_remarks, f"run_{input_name}", True)

    return fitz.open(f"tests/out/{metadata.notebook_name} _remarks.pdf")


@dataclass
class PageMetadata:
    notebook: NotebookMetadata
    page_number: int
    visual_description: str


@pytest.fixture
def visual_inspection(notebook: NotebookMetadata, remarks_document: Document, Page: PageMetadata, question: str):
    for file in notebook.rm_files:
        if "photo" in file:
            position = file["output_document_position"]
            img_output = remarks_document[position].get_pixmap()
            img_output.save(f"tests/out/{notebook.notebook_name} - {position} - Remarks.jpg")
            shutil.copy(file["photo"], f"tests/out/{notebook.notebook_name} - {position} - ReMarkable.jpg")


@pytest.fixture
def notebook(request):
    """Return the notebook fixture specified in the test's parameters"""
    return request.getfixturevalue(request.param)


@pytest.fixture
def obsidian_markdown(notebook):
    name = f"tests/out/{notebook.notebook_name} _obsidian.md"
    if os.path.isfile(name):
        with open(name) as f:
            return f.read()
    else:
        return None

@pytest.fixture
def remarks_document(notebook):
    """Run remarks on the notebook and return PDF"""
    return with_remarks(notebook)
