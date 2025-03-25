import pytest
from tests.NotebookMetadata import NotebookMetadata, PageMetadata
from RemarkableNotebookType import ReMarkableNotebookType
from remarks.metadata import ReMarkableAnnotationsFileHeaderVersion, ReMarkableDevice
from remarks.warnings import scrybble_warning_only_v6_supported, scrybble_warning_typed_text_highlighting_not_supported


@pytest.fixture
def markdown_tags_document():
    return NotebookMetadata(
        description="A document with a few tags",
        notebook_name="tags test",
        rmn_source="tests/in/v3 markdown tags.rmn",
        pdf_pages=2,
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        pages=[
            PageMetadata(
                tags=["#remarkable/obsidian"],
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V3,
                pdf_document_index=0,
            )
        ]
    )


@pytest.fixture
def gosper_notebook():
    return NotebookMetadata(
        description="A document with complex hand-drawn annotations",
        notebook_name="Gosper",
        rmn_source="tests/in/v2 notebook complex.rmn",
        pdf_pages=3,
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V3,
                pdf_document_index=0,
                warnings=[scrybble_warning_only_v6_supported]
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V3,
                pdf_document_index=1,
                warnings=[scrybble_warning_only_v6_supported]
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V3,
                pdf_document_index=2,
                warnings=[scrybble_warning_only_v6_supported]
            )
        ]
    )

@pytest.fixture
def highlights_document():
    return NotebookMetadata(
        description="""
        This document contains smart highlights in all colors on the first page.
        Similarly, it contains regular highlights on the second page.
        """,
        notebook_name="On computable numbers",
        rmn_source="tests/in/on computable numbers - RMPP - highlighter tool v6.rmn",
        notebook_type=ReMarkableNotebookType.PDF,
        pdf_pages=36,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=0,
                smart_highlights=[
                    "numbers may be described briefly as the real",
                    "numbers whose expressions as a decimal are calculable by finite means.",
                    "theory of functions",
                    "According to my definition, a number is computable",
                    "if its decimal can be written down by a machine.",
                    "In particular, I show that certain large classes",
                    "of",
                    "of numbers are computable.",
                    "The computable numbers do not, however, include",
                    "all definable numbers,",
                    "Although the class of computable numbers is so great, and in many",
                    "Avays similar to the class of real numbers, it is nevertheless enumerable.",
                ],
                photo={ReMarkableDevice.reMarkablePaperPro: "tests/in/on computable numbers - RMPP - highlighter tool v6 - page 1.jpeg"}
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=1,
                photo={ReMarkableDevice.reMarkablePaperPro: "tests/in/on computable numbers - RMPP - highlighter tool v6 - page 2.jpeg"}
            )
        ]
    )

@pytest.fixture
def highlights_multiline_document():
    return NotebookMetadata(
        description="""
        This document contains a multi-line smart highlight and multiple columns.
        """,
        notebook_name="multi column pdf.pdf",
        rmn_source="tests/in/multi-line highlights.rmn",
        notebook_type=ReMarkableNotebookType.PDF,
        pdf_pages=1,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=0,
                smart_highlights=[
                    "suddenly there came a tapping,",
                    "Eagerly I wished the morrow;—vainly I",
                    "had sought to borrow",
                    "Let my heart be still a moment and this",
                    "But, with mien of lord or lady, perched",
                    "above my chamber door—"
                ]
            )
        ]
    )

@pytest.fixture
def v5_document():
    return NotebookMetadata(
        notebook_name="1936 On Computable Numbers, with an Application to the Entscheidungsproblem - A. M. Turing",
        description="Alan Turing's \"On Computable Numbers\" with annotations from xochitl v5",  # No description provided; set it as an empty string
        rmn_source="tests/in/on computable numbers - v5.rmn",
        notebook_type=ReMarkableNotebookType.PDF,
        pdf_pages=36,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V5,
                pdf_document_index=0,
                warnings=[scrybble_warning_only_v6_supported],
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V5,
                pdf_document_index=1,
                smart_highlights=[],
                warnings=[scrybble_warning_only_v6_supported],
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V5,
                pdf_document_index=27,
                smart_highlights=[],
                warnings=[scrybble_warning_only_v6_supported],
            )
        ]
    )


@pytest.fixture
def black_and_white():
    return NotebookMetadata(
        notebook_name="B&W rmpp",
        description="""
        A simple notebook with only black and white on one page
        """,
        rmn_source="tests/in/rmpp - v6 - black and white only.rmn",
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        pdf_pages=1,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=0,
            )
        ]
    )


@pytest.fixture
def colored_document():
    return NotebookMetadata(
        notebook_name="Biological relativity",
        description="""
        A notebook with a few pages and various drawings.
        """,
        rmn_source="tests/in/rmpp - v6 - various colors.rmn",
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        pdf_pages=4,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=0,
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=1,
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=2,
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=3,
            )
        ]
    )

@pytest.fixture
def shader_notebook():
    return NotebookMetadata(
        notebook_name="Interviews",
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        description="A single page with 3 hand-drawn headings. Includes drawn icons, shaded with the shader tool.",
        rmn_source="tests/in/rmpp - shader tool.rmn",
        pdf_pages=1,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=0
            )
        ]
    )

@pytest.fixture
def typed_text_notebook():
    return NotebookMetadata(
        notebook_name="Text formatting",
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        description="A short notebook with 5 pages, containing almost exclusively typed text.",
        rmn_source="tests/in/rmpp - typed text.rmn",
        pdf_pages=5,
        pages=[
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=0,
                smart_highlights=[],
                typed_text="""# Text formatting

> [!WARNING] **Do not modify** this file
> This file is automatically generated by Scrybble and will be overwritten whenever this file in synchronized.
> Treat it as a reference.

## Pages

### [[Text formatting.pdf#page=1|Text formatting, page 1]]

#### Typed text

##### Hello! Heading

This is regular

**This is bold**

_This is italic_

###### This is medium text

###### **This is medium bold**

###### _This is medium italic_

_**This is regular bold italic**_

###### _**This is medium bold italic**_
- bullet 1
- bullet 2
- Mixed **bol**_**d ita**__lic_ _mess_ of text
- This is a very long line of text that will eventually wrap, I expect no newline in this strin
- [ ] This is a checkbox
- [x] This is a checked checkbox

##### **Bold heading**

##### _Italic heading_

##### **Mixed **_**heading**_
### [[Text formatting.pdf#page=2|Text formatting, page 2]]

#### Typed text

##### Text with corner dots
### [[Text formatting.pdf#page=3|Text formatting, page 3]]

#### Typed text

##### Text with drawn underlining
### [[Text formatting.pdf#page=4|Text formatting, page 4]]

#### Highlights
                   
> with highlight

#### Typed text

##### Text with highlight
### [[Text formatting.pdf#page=5|Text formatting, page 5]]

#### Typed text

##### Three _paragraphs with italic in one selection_

_p_

_THis is the end paragra_ph
""",
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=1,
                smart_highlights=[],
                typed_text=None,
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=2,
                smart_highlights=[],
                typed_text=None,
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=3,
                smart_highlights=[
                    # Note, this highlight is present on text that is typed on the ReMarkable itself,
                    # not on the original PDF.
                    " with highlight"
                ],
                warnings=[scrybble_warning_typed_text_highlighting_not_supported],
                typed_text=None,
            ),
            PageMetadata(
                rm_file_version=ReMarkableAnnotationsFileHeaderVersion.V6,
                pdf_document_index=4,
                smart_highlights=[],
                typed_text=None,
            )
        ]
    )

all_notebooks = [
    "markdown_tags_document",
    "gosper_notebook",
    "highlights_document",
    "highlights_multiline_document",
    "colored_document",
    "v5_document",
    "black_and_white",
    "shader_notebook",
    "typed_text_notebook"
]
