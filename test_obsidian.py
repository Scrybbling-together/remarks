from fitz import Document
from parsita import lit, reg, rep, Parser, opt, Failure, until
from returns.result import Success

from tests.notebook_fixtures import *

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
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_tags_present_on_a_page_are_in_the_markdown(notebook: NotebookMetadata, remarks_document: Document, obsidian_markdown: str | None):
    for page in notebook.pages:
        if page.tags:
            for tag in page.tags:
                assert_parser_succeeds(frontmatter << whatever, obsidian_markdown, [tag])

@pytest.mark.markdown
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_highlights_are_available_in_markdown(notebook: NotebookMetadata, remarks_document: Document, obsidian_markdown: str | None):
    # TODO: This test is not entirely reliable because it doesn't assert the sequence of the highlights
    for page in notebook.pages:
        if page.smart_highlights:
            for highlight in page.smart_highlights:
                assert_parser_succeeds(until(highlight) >> highlight << whatever, obsidian_markdown, highlight)

@pytest.mark.markdown
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_markdown_file_is_generated_only_if_relevant(notebook: NotebookMetadata, remarks_document, obsidian_markdown: None | str):
    """A markdown file is only generated iff it has:
       1. Typed text with the type folio or text tool
       2. Smart highlights
       3. Tags on the page
       Otherwise there will be no Markdown file"""
    for page in notebook.pages:
        if page.smart_highlights or page.typed_text or page.tags:
            assert type(obsidian_markdown) is str
            return
    assert obsidian_markdown is None

@pytest.mark.markdown
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_typed_text_is_present_in_markdown(notebook: NotebookMetadata, remarks_document: Document, obsidian_markdown: str | None):
    for page in notebook.pages:
        if page.typed_text:
            assert page.typed_text in obsidian_markdown

