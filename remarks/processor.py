import logging
import pathlib

import pymupdf
import pygame as pe
from pylibrm_lines import SceneTree, FailedToBuildTree, Renderer, SceneInfo
from pymupdf import Page
from rm_api.defaults import RM_SCREEN_SIZE
from rm_api.models import LocalDocument, Page

from remarks.Document import sanitize_filename
from remarks.output.ObsidianMarkdownFile import ObsidianMarkdownFile
from remarks.utils import rect_to_murect, ScalingTypes, frame_to_pixmap
from remarks.warnings import scrybble_warning_tree_failed_to_build


class DocumentProcessor:
    pdf_document: pymupdf.Document
    tree: SceneTree

    def __init__(self, document: LocalDocument, output_dir: pathlib.Path):
        self.document = document
        self.output_dir = output_dir
        self.obsidian_markdown = ObsidianMarkdownFile(document)

    @property
    def doc_pages(self):
        return self.document.content.c_pages.pages

    @property
    def renderer(self) -> Renderer:
        return self.tree.renderer

    @property
    def scene_info(self) -> SceneInfo | None:
        return self.tree.scene_info

    def run(self):
        # First, add page tags for ALL pages (including those without .rm files)
        self.obsidian_markdown.handle_page_tags()
        self.load_or_create_pdf()

        for i, page in enumerate(self.doc_pages):
            self.process_page(i, page)

        doc_name = sanitize_filename(self.document.metadata.visible_name)
        output_pdf_path = self.output_dir / f"{doc_name} _remarks.pdf"
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        self.pdf_document.save(output_pdf_path)

    def process_page(self, index: int, page: Page):
        logging.info(f"processing page {index + 1}, {page.id}")
        pdf_page = self.get_pdf_page(index, page)

        try:
            self.tree = SceneTree.from_document(self.document, page.id)
        except FailedToBuildTree:
            scrybble_warning_tree_failed_to_build.render_as_annotation(pdf_page)
            return

        page_bounds = self.get_page_bounds()
        pdf_page.set_mediabox(rect_to_murect(page_bounds, scaling=ScalingTypes.PDF_PTS))

        frame = frame_to_pixmap(
            self.renderer.get_frame_raw(
                page_bounds.x, page_bounds.y,
                *page_bounds.size,
                *page_bounds.size),
            page_bounds.size
        )
        pdf_page.insert_image(rect_to_murect(pe.Rect((0, 0, *page_bounds.size)), scaling=ScalingTypes.PDF_PTS), pixmap=frame)

    def get_page_bounds(self) -> pe.Rect:
        x1, y1, x2, y2 = 0, 0, *self.scene_info.paper_size
        layers = self.renderer.get_layers()

        if layers:
            for layer in layers:
                size_tracker = layer.size_tracker
                x1 = min(x1, size_tracker.left)
                y1 = min(y1, size_tracker.top)
                x2 = max(x2, size_tracker.right)
                y2 = max(y2, size_tracker.bottom)
        rect = pe.Rect((x1, y1, 0, 0))
        rect.size = (x2 - x1, y2 - y1)
        return rect

    def get_pdf_page(self, index: int, page: Page) -> pymupdf.Page:
        if not self.pdf_document:
            raise ValueError("PDF document is not loaded")
        if self.document.content.file_type == 'notebook':
            return self.pdf_document[index]
        if not page.redirect:
            raise ValueError(f"Page {page.id} does not have a redirect to a PDF page")
        if page.redirect.value < 0 or page.redirect.value >= len(self.pdf_document):
            raise IndexError(f"Page redirect index {page.redirect.value} is out of bounds for the PDF document")
        return self.pdf_document[page.redirect.value]

    def load_or_create_pdf(self):
        if self.document.content.file_type in ["pdf", "epub"]:
            file = self.document.file_uuid_map.get(f'{self.document.uuid}.pdf')
            if not file:
                raise FileNotFoundError("Could not find the PDF file for this document")
            pdf_path = self.document.get_file(file.hash)
            self.pdf_document = pymupdf.open(filename=pdf_path, filetype="pdf")
        else:
            self.pdf_document = pymupdf.open()  # Create a new empty PDF document
            for _ in self.doc_pages:
                self.pdf_document.new_page()  # Add a new blank page
