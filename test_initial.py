import pytest
from fitz import fitz
from parsita import lit, reg, rep, Parser, opt, Failure, until
from returns.result import Success

import remarks
from NotebookMetadata import NotebookMetadata
from RemarkableNotebookType import ReMarkableNotebookType
from pdf_test_support import assert_page_renders_without_warnings, assert_warning_exists
from remarks.metadata import ReMarkableAnnotationsFileHeaderVersion
from remarks.warnings import scrybble_warning_only_v6_supported


def with_remarks(metadata: NotebookMetadata):
    """Decorator to run remarks for a specific input directory."""
    input_name = metadata.rmn_source

    input_dir = input_name
    output_dir = "tests/out"

    if not getattr(with_remarks, f"run_{input_name}", False):
        remarks.run_remarks(input_dir, output_dir)
        setattr(with_remarks, f"run_{input_name}", True)

    return fitz.open(f"tests/out/{metadata.notebook_name} _remarks.pdf")


@pytest.fixture
def markdown_tags_document():
    return NotebookMetadata(
        description="""A document with a few tags""",
        notebook_name="tags test",
        rmn_source="tests/in/v3 markdown tags.rmn",
        pdf_pages=0,
        rm_files=[],
        notebook_type=ReMarkableNotebookType.NOTEBOOK,
        export_properties={
            "merged_pages": 2
        }
    )


@pytest.fixture
def gosper_notebook():
    return NotebookMetadata(
        description="""A document with complex hand-drawn annotations""",
        notebook_name="Gosper",
        rmn_source="tests/in/v2 notebook complex.rmn",
        pdf_pages=0,
        rm_files=[
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
                "output_document_position": 0,
                "input_document_position": 0
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
                "output_document_position": 1,
                "input_document_position": 1
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
                "output_document_position": 2,
                "input_document_position": 2
            }
        ],
        export_properties={
            "merged_pages": 3,
            "warnings": [
                {
                    "output_document_position": 0,
                    "warning": [scrybble_warning_only_v6_supported]
                },
                {
                    "output_document_position": 1,
                    "warning": [scrybble_warning_only_v6_supported]
                },
                {
                    "output_document_position": 2,
                    "warning": [scrybble_warning_only_v6_supported]
                }
            ]
        },
        notebook_type=ReMarkableNotebookType.NOTEBOOK
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
        rm_files=[
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 0,
                "photo": "tests/in/on computable numbers - RMPP - highlighter tool v6 - page 1.jpeg"
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 1,
                "photo": "tests/in/on computable numbers - RMPP - highlighter tool v6 - page 2.jpeg"
            }
        ],
        export_properties={
            "merged_pages": 36
        }
    )


@pytest.fixture
def v5_document():
    return NotebookMetadata(
        notebook_name="1936 On Computable Numbers, with an Application to the Entscheidungsproblem - A. M. Turing",
        description="",  # No description provided; set it as an empty string
        rmn_source="tests/in/on computable numbers - v5.rmn",
        notebook_type=ReMarkableNotebookType.PDF,
        pdf_pages=36,
        rm_files=[
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V5,
                "output_document_position": 0,
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V5,
                "output_document_position": 1,
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V5,
                "output_document_position": 27
            }
        ],
        export_properties={
            "merged_pages": 36,
            "warnings": [
                {
                    "warning": [scrybble_warning_only_v6_supported],
                    "output_document_position": 0,
                },
                {
                    "warning": [scrybble_warning_only_v6_supported],
                    "output_document_position": 1,
                },
                {
                    "warning": [scrybble_warning_only_v6_supported],
                    "output_document_position": 27
                }
            ]
        }
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
        rm_files=[
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 0
            }
        ],
        export_properties={
            "merged_pages": 1
        }
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
        rm_files=[
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 0
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 1
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 2
            },
            {
                ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
                "output_document_position": 3
            }
        ],
        export_properties={
            "merged_pages": 4
        }
    )


all_notebooks = [
    "markdown_tags_document",
    "gosper_notebook",
    "highlights_document",
    "colored_document",
    "v5_document",
    "black_and_white"
]


@pytest.fixture
def notebook(request):
    """Return the notebook fixture specified in the test's parameters"""
    return request.getfixturevalue(request.param)


@pytest.fixture
def obsidian_markdown(notebook):
    with open(f"tests/out/{notebook.notebook_name} _obsidian.md") as f:
        return f.read()


@pytest.fixture
def page():
    pass
    # remarks_generated_pdf = Document(f"tests/out/{metadata.notebook_name} _remarks.pdf")
    # for file in metadata.rm_files:
    #     if "photo" in file:
    #         # show the photo next to the generated page
    #         # - [ ] Get the generated page from the output
    #         position = file["output_document_position"]
    #         img_output = remarks_generated_pdf[position].get_pixmap()
    #         img_output.save(f"tests/out/{metadata.notebook_name} - {position} - Remarks.jpg")
    #         shutil.copy(file["photo"], f"tests/out/{metadata.notebook_name} - {position} - ReMarkable.jpg")

@pytest.fixture
def remarks_document(notebook):
    """Run remarks on the notebook and return PDF"""
    return with_remarks(notebook)


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
def test_valid_pdf(notebook, remarks_document):
    assert remarks_document.is_pdf


@pytest.mark.pdf
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_correct_output_page_count(notebook, remarks_document):
    assert remarks_document.page_count == notebook.export_properties["merged_pages"]


@pytest.mark.pdf
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_warnings_match_specification(notebook, remarks_document):
    # Get expected warnings from metadata
    expected_warnings = notebook.export_properties.get("warnings", [])

    # For each page, verify warnings
    for page_num in range(remarks_document.page_count):
        page_warnings = [w for w in expected_warnings
                         if w["output_document_position"] == page_num]

        if page_warnings:
            # Verify each expected warning exists
            for warning_spec in page_warnings:
                for warning in warning_spec["warning"]:
                    assert_warning_exists(remarks_document, page_num, warning)
        else:
            # If no warnings specified for this page, verify page is clean
            assert_page_renders_without_warnings(remarks_document, page_num)


r"""
 __  __            _       _                     
|  \/  |          | |     | |                    
| \  / | __ _ _ __| | ____| | _____      ___ __  
| |\/| |/ _` | '__| |/ / _` |/ _ \ \ /\ / / '_ \ 
| |  | | (_| | |  |   < (_| | (_) \ V  V /| | | |
|_|  |_|\__,_|_|  |_|\_\__,_|\___/ \_/\_/ |_| |_|

Lessons about parsita.

1. When invoking a parser, you _must_ consume all the tokens until the EOD or you will get a failure
   You can do this with 
   `{...} << whatever`
2. When you want to extract _one_ value out of a big text. You can say the following:
   parser_that_must_exist_around_it >> parser_that_follows >> another_parser << the_parser_you_care_about >> after_the_parser_you_care_about
   So:
   `{...} >> yes << whatever` => `Success<yes>`
3. Lambdas are evil. Do not use lambdas to create abstractions.
   While it may seem attractive to write a lambda to express a common pattern, this is not a good idea.
   The operators in parsita have specific meaning, and parsita is a language expressed with operators.
   When you write a function, the result of the operator is lost.
"""


def assert_parser_succeeds(parser: Parser, input_string: str, expected_output=None):
    result = parser.parse(input_string)
    match result:
        case Success(value):
            output = value
            if expected_output:
                assert expected_output == output
        case Failure(error):
            raise error
    assert type(result) is Success, result.failure()


any_char = reg(r'.') | lit("\n")
whatever = rep(any_char)
newline = lit('\n')

to_newline = reg(r'[^\n]+')

obsidian_tag = reg(r"#([a-z/])+")
frontmatter = opt(
    lit('---') >> newline >>
    lit("tags") >> lit(":\n") >> lit("- ") >> lit("'") >> obsidian_tag << lit("'") << rep(newline) <<
    lit("---") << rep(newline)
)
autogeneration_warning = lit("""> [!WARNING] **Do not modify** this file
> This file is automatically generated by Scrybble and will be overwritten whenever this file in synchronized.
> Treat it as a reference.""")
h1_tag = lit("# ")
h2_tag = lit("## ")
h3_tag = lit("### ")
h4_tag = lit("#### ")
h5_tag = lit("##### ")
h6_tag = lit("###### ")

@pytest.mark.markdown
@pytest.mark.parametrize("notebook", ["markdown_tags_document"], indirect=True)
def test_yaml_frontmatter_is_valid(notebook, obsidian_markdown):
    assert_parser_succeeds(frontmatter << whatever, obsidian_markdown, ["#remarkable/obsidian"])

@pytest.mark.markdown
@pytest.mark.parametrize("notebook", ["highlights_document"], indirect=True)
def test_highlights_are_available_in_markdown(notebook, obsidian_markdown):
    # yellow marker
    smart_highlight_one = "numbers may be described briefly as the real numbers whose expressions as a decimal are calculable by finite means"
    # blue marker
    smart_highlight_two = "theory of functions"
    # green marker
    smart_highlight_three = "According to my definition, a number is computable if its decimal can be written down by a machine."
    # pink marker
    smart_highlight_four = "In particular, I show that certain large classes of of numbers are computable."
    # grey marker
    # smart_highlight_five = "Although the class of computable numbers is so great, and in many ways similar to the class of real numbers, it is nevertheless enumerable."

    assert_parser_succeeds(until(smart_highlight_one) >> smart_highlight_one << whatever, obsidian_markdown, smart_highlight_one)
    assert_parser_succeeds(until(smart_highlight_two) >> smart_highlight_two << whatever, obsidian_markdown, smart_highlight_two)
    assert_parser_succeeds(until(smart_highlight_three) >> smart_highlight_three << whatever, obsidian_markdown, smart_highlight_three)
    assert_parser_succeeds(until(smart_highlight_four) >> smart_highlight_four << whatever, obsidian_markdown, smart_highlight_four)
    # assert_parser_succeeds(until(smart_highlight_five) >> smart_highlight_four << whatever, obsidian_markdown, smart_highlight_five)
