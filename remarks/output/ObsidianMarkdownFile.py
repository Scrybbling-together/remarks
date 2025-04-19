import os
from typing import List, Dict

import yaml
from jinja2 import Environment, FileSystemLoader
from rmscene.scene_items import GlyphRange, ParagraphStyle
from rmscene.text import Paragraph

from remarks.Document import Document


def render_paragraph(paragraph: Paragraph):
    paragraph_content = ""
    for st in paragraph.contents:
        st_text = str(st)
        if st.properties['font-weight'] == "bold":
            st_text = f"**{st_text}**"
        if st.properties['font-style'] == "italic":
            st_text = f"_{st_text}_"
        paragraph_content += st_text

    if paragraph.style.value == ParagraphStyle.PLAIN:
        return f"\n{paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.BOLD:
        return f"\n###### {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.HEADING:
        return f"\n##### {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.BULLET or paragraph.style.value == ParagraphStyle.BULLET2:
        return f"- {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.CHECKBOX:
        return f"- [ ] {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.CHECKBOX_CHECKED:
        return f"- [x] {paragraph_content}\n"

    return paragraph_content


class RMPage:
    def __init__(self):
        self.highlights: List[GlyphRange] = []
        self.tags: List[str] = []
        self.text: None | list[Paragraph] = None


def merge_highlight_texts(h1: GlyphRange, h2: GlyphRange, distance: int) -> str:
    """
    Merge the text of two highlights based on their relative positions.

    Args:
        h1: The first highlight (comes earlier in the text)
        h2: The second highlight
        distance: The calculated distance between the highlights

    Returns:
        str: The merged text
    """
    # Case 1: B starts after A ends (positive distance)
    if distance > 0:
        # We need to add the gap characters
        # Since we don't have access to the original text, use placeholder for the gap
        gap = " " * distance  # Using spaces as placeholder for the gap
        text = h1.text + gap + h2.text

    # Case 2: B starts before A ends (overlap)
    else:
        # Calculate the overlap amount
        overlap = -distance

        # The first part is all of A's text
        merged_first_part = h1.text

        # For the second part, we need to skip the overlapped characters from B
        # This assumes the overlapped text is identical in both highlights
        merged_second_part = h2.text[overlap:] if overlap < len(h2.text) else ""

        text = merged_first_part + merged_second_part

    return " ".join(text.split())


def calculate_highlight_distance(h1: GlyphRange, h2: GlyphRange):
    if h1.start > h2.start:
        h1, h2 = h2, h1
    end_of_h1 = h1.start + h1.length
    distance = h2.start - end_of_h1

    if h1.color != h2.color:
        return float('inf'), end_of_h1, h1, h2

    return distance, end_of_h1, h1, h2


def merge_highlights(highlights: List[GlyphRange]):
    max_gap_threshold = 3
    merged_highlights = list(filter(lambda h: h is not None and type(h.start) is int, highlights.copy()))
    # Continue until no more changes
    while True:
        # Sort by starting position
        merged_highlights.sort(key=lambda h: h.start)

        # Flag to track if any merges happened
        merged_any = False

        # Check all pairs for possible merges
        i = 0
        while i < len(merged_highlights) - 1:
            j = i + 1
            while j < len(merged_highlights):
                h1 = merged_highlights[i]
                h2 = merged_highlights[j]

                # Calculate distance (ensuring A comes before B)
                distance, end_of_h1, h1, h2 = calculate_highlight_distance(h1, h2)

                # If they should be merged
                if distance <= max_gap_threshold:
                    # Create merged highlight
                    new_start = min(h1.start, h2.start)
                    new_end = max(end_of_h1, h2.start + h2.length)
                    new_length = new_end - new_start

                    # Create new highlight
                    merged_highlight = GlyphRange(
                        start=new_start,
                        length=new_length,
                        text=merge_highlight_texts(h1, h2, distance),
                        color=h1.color,
                        rectangles=h1.rectangles + h2.rectangles
                    )

                    # Replace A with merged highlight and remove B
                    merged_highlights[i] = merged_highlight
                    merged_highlights.pop(j)

                    merged_any = True
                    # Don't increment j since we removed an element
                else:
                    j += 1

            i += 1

        # If no merges happened, we're done
        if not merged_any:
            break
    print(merged_highlights)
    return merged_highlights


class ObsidianMarkdownFile:
    def __init__(self, document: Document):
        self.pages: Dict[int, RMPage] = {}
        self.document = document

    def retrieve_page(self, index: int):
        if not index in self.pages:
            page = RMPage()
            self.pages[index] = page
        else:
            page = self.pages[index]

        return page

    def save(self, location: str):
        if not self.document.rm_tags and not self.pages:
            return

        frontmatter = {"tags": [f"#remarkable/{tag}" for tag in self.document.rm_tags]}

        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        template = env.get_template('obsidian_markdown.md.jinja')

        content = template.render(**{
            'document': self.document,
            'frontmatter': yaml.dump(frontmatter, indent=2) if frontmatter["tags"] else None,
            'pages': self.pages,
            'sorted_pages': sorted(self.pages.items()),
            'render_paragraph': render_paragraph
        })

        with open(f"{location} _obsidian.md", "w") as f:
            f.write(content)

    def add_highlights(
        self, page_idx: int, highlights: List[GlyphRange]
    ):
        if not highlights:
            return

        self.retrieve_page(page_idx).highlights = merge_highlights(highlights)

    def add_text(self, page_idx: int, text):
        if not text:
            return
        self.retrieve_page(page_idx).text = text["text"].contents
