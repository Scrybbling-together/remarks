from dataclasses import dataclass
from typing import List

from fitz import Document
from parsita import lit, reg, rep, Parser, opt, Failure, until, eof, ParserContext
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


@dataclass
class Page:
    number: int
    document_name: str
    highlights: List[str]
    typed_text: str


@dataclass
class Highlights:
    highlights: List[str]

@dataclass
class Document:
    name: str
    tags: List[str]
    pages: List[Page]


def to_page(page_content: List) -> Page:
    [document_name, page_number], highlights, typed_text = page_content
    return Page(page_number, document_name, highlights[0] if highlights else [], typed_text)

def to_document(a) -> Document:
    tags, name, pages_list = a
    return Document(name=name, tags=tags[0], pages=pages_list[0] if pages_list else [])


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


class ObsidianDocumentParser(ParserContext):
    any_char = reg(r'.') | lit("\n")
    whatever = rep(any_char)

    newline = lit('\n')

    h1_tag = lit("# ")
    h2_tag = lit("## ")
    h3_tag = lit("### ")
    h4_tag = lit("#### ")
    h5_tag = lit("##### ")
    h6_tag = lit("###### ")

    # reMarkable allows many characters that aren't allowed in many other systems.
    # This is a regular expression that matches valid reMarkable filenames
    document_name = reg(r"[\w .,-;()\$&@\"\?!'[\]{\}%*\+=_\\<>€£¥•¿]+")
    document_title = h1_tag >> document_name << rep(newline)

    to_newline = reg(r'[^\n]+')

    filename_frontmatter = lit('scrybble_filename: ') >> until(newline)
    timestamp_frontmatter = lit('scrybble_timestamp: ') >> until(newline)
    obsidian_tag = reg(r"#([a-z/])+")
    tags_frontmatter = opt(lit("tags") >> lit(":\n") >> lit("- ") >> lit("'") >> obsidian_tag << lit("'") << rep(
            newline))

    frontmatter = opt(
        lit('---') >> newline << filename_frontmatter >> newline >> timestamp_frontmatter << newline >> tags_frontmatter << lit("---") << rep(newline))
    autogeneration_warning = lit("""> [!WARNING] **Do not modify** this file
> This file is automatically generated by Scrybble and will be overwritten whenever this file in synchronized.
> Treat it as a reference.""") << rep(newline)

    ## Links
    link_start, link_end = lit("[["), lit("]]")
    page_number = reg(r"\d+") > int
    pdf_anchor = lit("#")
    link_clean_title_operator = "|"
    # Takes a pdf link like
    # "### [[On computable numbers.pdf#page=1|On computable numbers, page 1]]"
    # and returns the document name and page as a 2-tuple, [str, int]
    # <Success: ["On computable numbers", 1]>
    pdf_link = h3_tag >> link_start >> document_name >> pdf_anchor >> lit(
        "page=") >> page_number >> link_clean_title_operator >> until(", page ") << lit(", page ") & page_number << link_end

    ## Pages
    highlights_title = h4_tag >> "Highlights"
    typed_text_title = h4_tag >> "Typed text"
    page_title = h2_tag >> lit("Pages") << rep(newline)
    highlight = (lit("> ") >> until("\n\n"))
    highlights = highlights_title >> rep(rep(newline) >> highlight) << rep(newline)
    typed_texts = typed_text_title >> rep(newline) >> until((newline >> h3_tag) | (newline >> h4_tag) | eof) << rep(newline)
    pages = opt(page_title >> rep(newline) >>
                rep(
                    (pdf_link & rep(newline) >>
                      opt(highlights << rep(newline)) &
                      opt(typed_texts << rep(newline))
                    ) > to_page))

    document = (frontmatter & document_title << autogeneration_warning & pages) > to_document


# Note: This test is incorrect. Document tags and page tags are separate things.
# This confuses the two, testing page tags being present in the document metadata.
# Needs to be split up into two tests.
# One for page tags, and one for document tags.
@pytest.mark.unfinished_feature
@pytest.mark.markdown
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_tags_present_on_a_page_are_in_the_markdown(notebook: NotebookMetadata, remarks_document: Document,
                                                    obsidian_markdown: str | None):
    if obsidian_markdown:
        for page in notebook.pages:
            if page.tags:
                document = ObsidianDocumentParser.document.parse(obsidian_markdown).unwrap()
                for tag in page.tags:
                    assert tag in document.tags


@pytest.mark.markdown
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_filenames_are_sanitized(notebook: NotebookMetadata, remarks_document: Document, obsidian_markdown: str | None):
    """
    Filenames are sanitized, special tokens are removed.
    Obsidian filenames cannot contain the following special tokens:
    :/\
    Additionally, Obsidian recommends you not to use these characters in filenames
    because they will break links:
    #[]^|
    Within remarks, we will replace these characters with a _
    """
    if obsidian_markdown:
        characters_forbidden_in_obsidian_links = "#[]^|:\\/"
        result = ObsidianDocumentParser.document.parse(obsidian_markdown).unwrap()
        for char in characters_forbidden_in_obsidian_links:
            assert char not in result.name


@pytest.mark.markdown
@pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
def test_highlights_are_available_in_markdown(notebook: NotebookMetadata, remarks_document: Document,
                                              obsidian_markdown: str | None):
    """For highlights, there are two important measures we can test.
    First of all, we need to make sure that the order is the same as it appears on the page.
    This is captured in the NotebookMetadata, the order is provided by whoever makes the metadata object.

    Second of all, each highlight item should appear as its own quotation block in Markdown:

    ```
    > highlight 1

    > highlight 2
    ```

    And not

    ```
    > highlight 1
    > highlight 2
    """
    if obsidian_markdown:
        result = ObsidianDocumentParser.document.parse(obsidian_markdown).unwrap()

        for page in notebook.pages:
            if page.merged_highlights:
                corresponding_page = result.pages[page.pdf_document_index]

                len1 = len(corresponding_page.highlights)
                len2 = len(page.merged_highlights)
                assert len1 == len2, f"The length of the parsed highlights {len1} differs from the length of the expected highlights {len2}"
                for i, highlight in enumerate(page.merged_highlights):
                    assert corresponding_page.highlights[i] == page.merged_highlights[i]

# @pytest.mark.markdown
# @pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
# def test_markdown_file_is_generated_only_if_relevant(notebook: NotebookMetadata, remarks_document,
#                                                      obsidian_markdown: None | str):
#     """A markdown file is only generated iff it has:
#        1. Typed text with the type folio or text tool
#        2. Smart highlights
#        3. Tags on the page
#        Otherwise there will be no Markdown file"""
#     for page in notebook.pages:
#         if page.smart_highlights or page.typed_text or page.tags:
#             assert type(obsidian_markdown) is str
#             return
#     assert obsidian_markdown is None
#
#
# @pytest.mark.markdown
# @pytest.mark.parametrize("notebook", all_notebooks, indirect=True)
# def test_typed_text_is_present_in_markdown(notebook: NotebookMetadata, remarks_document: Document,
#                                            obsidian_markdown: str | None):
#     for page in notebook.pages:
#         if page.typed_text:
#             assert page.typed_text in obsidian_markdown
