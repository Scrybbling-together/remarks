import pytest
from fitz import fitz
from parsita import lit, reg, rep, Parser, opt, Failure, until
from returns.result import Success

from NotebookMetadata import NotebookMetadata
from RemarkableNotebookType import ReMarkableNotebookType
from remarks.metadata import ReMarkableAnnotationsFileHeaderVersion
from test_support import with_remarks
from pdf_test_support import is_valid_pdf, assert_scrybble_warning_appears_on_page, assert_page_renders_without_warnings

markdown_tags = NotebookMetadata(
    description="""A document with a few tags""",
    notebook_name="tags test",
    rmn_source="tests/in/v3_markdown_tags",
    pdf_pages=0,
    rm_files=[],
    notebook_type=ReMarkableNotebookType.NOTEBOOK,
    export_properties={}
)

gosper_notebook_metadata = NotebookMetadata(
    description="""A document with complex hand-drawn annotations""",
    notebook_name="Gosper",
    rmn_source="tests/in/v2_notebook_complex",
    pdf_pages=0,
    rm_files=[
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
            "output_document_position": 0
        },
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
            "output_document_position": 1
        },
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
            "output_document_position": 2
        }
    ],
    export_properties={
        "merged_pages": 3
    },
    notebook_type=ReMarkableNotebookType.NOTEBOOK
)

document_with_various_highlights_metadata = NotebookMetadata(
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
            "output_document_position": 0
        },
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
            "output_document_position": 1
        }
    ],
    export_properties={}
)

on_computable_numbers_metadata = NotebookMetadata(
    notebook_name="1936 On Computable Numbers, with an Application to the Entscheidungsproblem - A. M. Turing",
    description="",  # No description provided; set it as an empty string
    rmn_source="tests/in/on-computable-numbers",
    notebook_type=ReMarkableNotebookType.PDF,
    pdf_pages=36,  # From the 'pdf_pages' field in the original dictionary
    rm_files=[
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V5,
            "output_document_position": 0
        },
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V5,
            "output_document_position": 1
        },
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V5,
            "output_document_position": 27
        }
    ],
    export_properties={
        "merged_pages": 36  # Metadata on the exported notebook
    }
)

black_and_white_metadata = NotebookMetadata(
    notebook_name="B&W rmpp",
    description="""
    A simple notebook with only black and white on one page
    """,
    rmn_source="tests/in/rmpp - v6 - black and white only.rmn",
    notebook_type=ReMarkableNotebookType.NOTEBOOK,
    pdf_pages=1,  # Mapped `merged_pages` to `pdf_pages` since it seems equivalent in intent
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

colored_real_document_metadata = NotebookMetadata(
    notebook_name="Biological relativity",
    description="""
    A notebook with a few pages and various drawings.
    """,
    rmn_source="tests/in/rmpp - v6 - various colors.rmn",
    notebook_type=ReMarkableNotebookType.NOTEBOOK,
    pdf_pages=4,  # From 'merged_pages' in the 'export_properties'
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
        "merged_pages": 4  # Metadata on the exported notebook
    }
)


r"""
 _____  _____  ______ 
|  __ \|  __ \|  ____|
| |__) | |  | | |__   
|  ___/| |  | |  __|  
| |    | |__| | |     
|_|    |_____/|_|     
"""

@with_remarks(on_computable_numbers_metadata)
def test_v5_document():
    on_computable_numbers_rmc = fitz.open(f"tests/out/{on_computable_numbers_metadata.notebook_name} _remarks.pdf")
    assert is_valid_pdf(on_computable_numbers_rmc)
    assert on_computable_numbers_rmc.page_count == on_computable_numbers_metadata.export_properties["merged_pages"]

    # There should be a warning, since v5 is not yet supported by the rmc-renderer
    assert_scrybble_warning_appears_on_page(on_computable_numbers_rmc, on_computable_numbers_metadata.rm_files[0]['output_document_position'])
    assert_scrybble_warning_appears_on_page(on_computable_numbers_rmc, on_computable_numbers_metadata.rm_files[1]['output_document_position'])
    assert_scrybble_warning_appears_on_page(on_computable_numbers_rmc, on_computable_numbers_metadata.rm_files[2]['output_document_position'])


@with_remarks(black_and_white_metadata)
def test_renders_notebook_with_single_v6_page_properly():
    black_and_white_rmc = fitz.open(f"tests/out/{black_and_white_metadata.notebook_name} _remarks.pdf")
    assert is_valid_pdf(black_and_white_rmc)
    assert black_and_white_rmc.page_count == black_and_white_metadata.export_properties["merged_pages"]

    assert_page_renders_without_warnings(black_and_white_rmc, black_and_white_metadata.rm_files[0]['output_document_position'])


@with_remarks(colored_real_document_metadata)
def test_renders_notebook_with_rmpp_v6_colors_properly():
    colored_document = fitz.open(f"tests/out/{colored_real_document_metadata.notebook_name} _remarks.pdf")
    assert is_valid_pdf(colored_document)
    assert colored_document.page_count == colored_real_document_metadata.export_properties["merged_pages"]

    assert_page_renders_without_warnings(colored_document, colored_real_document_metadata.rm_files[0]['output_document_position'])
    assert_page_renders_without_warnings(colored_document, colored_real_document_metadata.rm_files[0]['output_document_position'])
    assert_page_renders_without_warnings(colored_document, colored_real_document_metadata.rm_files[0]['output_document_position'])
    assert_page_renders_without_warnings(colored_document, colored_real_document_metadata.rm_files[0]['output_document_position'])


@with_remarks(gosper_notebook_metadata)
def test_pdf_output():
    gosper_rmc = fitz.open(f"tests/out/{gosper_notebook_metadata.notebook_name} _remarks.pdf")
    assert is_valid_pdf(gosper_rmc)
    assert gosper_rmc.page_count == gosper_notebook_metadata.export_properties["merged_pages"]

    # There should be a warning, since v3 is not yet supported by the rmc-renderer
    assert_scrybble_warning_appears_on_page(gosper_rmc, gosper_notebook_metadata.rm_files[0]['output_document_position'])
    assert_scrybble_warning_appears_on_page(gosper_rmc, gosper_notebook_metadata.rm_files[1]['output_document_position'])
    assert_scrybble_warning_appears_on_page(gosper_rmc, gosper_notebook_metadata.rm_files[2]['output_document_position'])


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


@with_remarks(markdown_tags)
@pytest.mark.markdown
def test_yaml_frontmatter_is_valid():
    with open('tests/out/tags test _obsidian.md') as f:
        content = f.read()
        assert_parser_succeeds(frontmatter << whatever, content, ["#remarkable/obsidian"])

@with_remarks(document_with_various_highlights_metadata)
@pytest.mark.markdown
def test_highlights_are_available_in_markdown():
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

    with open(f"tests/out/{document_with_various_highlights_metadata.notebook_name} _obsidian.md") as f:
        content = f.read()
        assert_parser_succeeds(until(smart_highlight_one) >> smart_highlight_one << whatever, content, smart_highlight_one)
        assert_parser_succeeds(until(smart_highlight_two) >> smart_highlight_two << whatever, content, smart_highlight_two)
        assert_parser_succeeds(until(smart_highlight_three) >> smart_highlight_three << whatever, content, smart_highlight_three)
        assert_parser_succeeds(until(smart_highlight_four) >> smart_highlight_four << whatever, content, smart_highlight_four)
        # assert_parser_succeeds(until(smart_highlight_five) >> smart_highlight_four << whatever, content, smart_highlight_five)


