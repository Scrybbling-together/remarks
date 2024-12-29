from enum import Enum

import pytest
from fitz import fitz
from parsita import lit, reg, rep, Parser, opt, until, Failure
from returns.result import Success

from remarks.metadata import ReMarkableAnnotationsFileHeaderVersion
from test_support import with_remarks
from pdf_test_support import is_valid_pdf, assert_scrybble_warning_appears_on_page, assert_page_renders_without_warnings


class ReMarkableNotebookType(Enum):
    NOTEBOOK = "Notebook"
    EBOOK = "EBook"
    PDF = "PDF"


# A metadata object MUST be entirely hand-crafted and hand-checked
gosper_notebook = {
    # ReMarkable document name
    "notebook_name": "Gosper",
    # Where the ReMarkable document can be found
    ".rmn_source": "tests/in/v2_notebook_complex",
    "notebook_type": ReMarkableNotebookType.NOTEBOOK,
    # The amount of pages that are coming from a source PDF
    "pdf_pages": 0,
    ".rm_files": [
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
            "output_document_position": 0
        }, {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
            "output_document_position": 1
        }, {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V3,
            "output_document_position": 2
        }
    ]
}

on_computable_numbers = {
    # ReMarkable document name
    "notebook_name": "1936 On Computable Numbers, with an Application to the Entscheidungsproblem - A. M. Turing",
    # Where the ReMarkable document can be found
    ".rmn_source": "tests/in/on-computable-numbers",
    "notebook_type": ReMarkableNotebookType.PDF,
    # The amount of pages that are coming from a source PDF
    "pdf_pages": 36,
    ".rm_files": [
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
    ]
}

black_and_white_document = {
    "notebook_name": "B&W rmpp",
    "description": """
    A simple notebook with only black and white on one page
    """,
    ".rmn_source": "tests/in/rmpp - v6 - black and white only.rmn",
    "notebook_type": ReMarkableNotebookType.NOTEBOOK,
    ".rm_files": [
        {
            ".rm_file_version": ReMarkableAnnotationsFileHeaderVersion.V6,
            "output_document_position": 0
        }
    ]
}


r"""
 _____  _____  ______ 
|  __ \|  __ \|  ____|
| |__) | |  | | |__   
|  ___/| |  | |  __|  
| |    | |__| | |     
|_|    |_____/|_|     
"""

@with_remarks(on_computable_numbers['.rmn_source'])
def test_v5_document():
    on_computable_numbers_rmc = fitz.open(f"tests/out/{on_computable_numbers['notebook_name']} _remarks.pdf")
    assert is_valid_pdf(on_computable_numbers_rmc)
    assert on_computable_numbers_rmc.page_count == on_computable_numbers['pdf_pages']

    # There should be a warning, since v5 is not yet supported by the rmc-renderer
    assert_scrybble_warning_appears_on_page(on_computable_numbers_rmc, on_computable_numbers['.rm_files'][0]['output_document_position'])
    assert_scrybble_warning_appears_on_page(on_computable_numbers_rmc, on_computable_numbers['.rm_files'][1]['output_document_position'])
    assert_scrybble_warning_appears_on_page(on_computable_numbers_rmc, on_computable_numbers['.rm_files'][2]['output_document_position'])

@with_remarks(black_and_white_document['.rmn_source'])
def test_renders_notebook_with_single_v6_page_properly():
    black_and_white_rmc = fitz.open(f"tests/out/{black_and_white_document['notebook_name']} _remarks.pdf")
    assert is_valid_pdf(black_and_white_rmc)
    assert black_and_white_rmc.page_count == 1

    assert_page_renders_without_warnings(black_and_white_rmc, black_and_white_document['.rm_files'][0]['output_document_position'])


@with_remarks(gosper_notebook['.rmn_source'])
def test_pdf_output():
    gosper_rmc = fitz.open(f"tests/out/{gosper_notebook['notebook_name']} _remarks.pdf")
    assert is_valid_pdf(gosper_rmc)
    assert gosper_rmc.page_count == len(gosper_notebook[".rm_files"])

    # There should be a warning, since v3 is not yet supported by the rmc-renderer
    assert_scrybble_warning_appears_on_page(gosper_rmc, gosper_notebook['.rm_files'][0]['output_document_position'])
    assert_scrybble_warning_appears_on_page(gosper_rmc, gosper_notebook['.rm_files'][1]['output_document_position'])
    assert_scrybble_warning_appears_on_page(gosper_rmc, gosper_notebook['.rm_files'][2]['output_document_position'])


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
   `no >> yes << no` => `Success<yes>`
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
h = lambda n, c: lit(n + " ") >> c

@with_remarks("tests/in/highlighter-test")
@pytest.mark.markdown
def test_generated_markdown_has_autogeneration_warning():
    has_warning = (until(autogeneration_warning) << autogeneration_warning >> whatever)
    with open("tests/out/docsfordevelopers _obsidian.md") as f:
        assert_parser_succeeds(has_warning, f.read())

@with_remarks("tests/in/v3_markdown_tags")
@pytest.mark.markdown
def test_yaml_frontmatter_is_valid():
    with open('tests/out/tags test _obsidian.md') as f:
        content = f.read()
        assert_parser_succeeds(frontmatter << whatever, content, ["#remarkable/obsidian"])


# @with_remarks("tests/in/v3_markdown_tags")
# @with_remarks("tests/in/highlighter-test")
# @pytest.mark.markdown
# def test_generated_markdown_heading_is_positioned_correctly():
#     rmdoc_title = h("#", to_newline)
#
#     with open("tests/out/docsfordevelopers _obsidian.md") as f:
#         content = f.read()
#         assert_parser_succeeds(frontmatter >> rmdoc_title << whatever, content, "docsfordevelopers")
#     with open("tests/out/tags test _obsidian.md") as f:
#         content = f.read()
#         assert_parser_succeeds(frontmatter >> rmdoc_title << whatever, content, "tags test")



# @with_remarks("tests/in/v3_typed_text")
# def test_something():
#     raise Exception("hi")
