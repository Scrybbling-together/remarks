import pathlib

from jinja2 import Environment, FileSystemLoader
from rmscene.scene_items import ParagraphStyle
from rmscene.text import Paragraph

from remarks.Document import Document

from .obsidian_markdown import ObsidianMarkdownFile

def render_paragraph(paragraph: Paragraph):
    paragraph_content = ""
    for st in paragraph.contents:
        st_text = str(st)
        if st.properties['font-weight'] == "bold":
            st_text = f"*{st_text}*"
        if st.properties['font-style'] == "italic":
            st_text = f"/{st_text}/"
        paragraph_content += st_text

    if paragraph.style.value == ParagraphStyle.PLAIN:
        return f"\n{paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.BOLD:
        return f"\n*{paragraph_content}*\n"
    elif paragraph.style.value == ParagraphStyle.HEADING:
        return f"\n**** {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.BULLET or paragraph.style.value == ParagraphStyle.BULLET2:
        return f"- {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.CHECKBOX:
        return f"- [ ] {paragraph_content}\n"
    elif paragraph.style.value == ParagraphStyle.CHECKBOX_CHECKED:
        return f"- [x] {paragraph_content}\n"

    return paragraph_content


class ObsidianOrgFile(ObsidianMarkdownFile):
    def __init__(self, document: Document):
        super().__init__(document)

    def save(self, output_file: pathlib.Path):
        env = Environment(loader=FileSystemLoader(pathlib.Path(__file__).parent))
        template = env.get_template('org_noter.org.jinja')

        content = template.render(**{
            'document': self.document,
            'pages': self.pages,
            'sorted_pages': sorted(self.pages.items()),
            'render_paragraph': render_paragraph
        })

        with open(output_file, "w") as f:
            f.write(content)

    @classmethod
    def from_obsidian_markdown(cls, obsidian_markdown: ObsidianMarkdownFile) -> "ObsidianOrgFile":
        obsidian_org = ObsidianOrgFile(obsidian_markdown.document)
        obsidian_org.pages = obsidian_markdown.pages
        return obsidian_org
