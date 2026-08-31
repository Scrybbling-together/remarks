import logging
import pathlib
from typing import Tuple

import pymupdf
import pygame as pe
from pylibrm_lines import SceneTree, FailedToBuildTree, Renderer, SceneInfo, set_debug_mode
from pylibrm_lines.renderer import BACKDROP_ALIGN_TOP_CENTER, PEN_HIGHLIGHTER
from pylibrm_lines.scene_items.glyph_range import GlyphRangeItem
from pylibrm_lines.scene_items.line import LineItem
from rm_api.defaults import RM_SCREEN_SIZE
from rm_api.models import LocalDocument, Page

from remarks.Document import sanitize_filename
from remarks.output.ObsidianMarkdownFile import ObsidianMarkdownFile
from remarks.utils import rect_to_murect, ScalingTypes, frame_to_pixmap, PDF_SCALING
from remarks.warnings import scrybble_warning_tree_failed_to_build


class DocumentProcessor:
    pdf_document: pymupdf.Document
    tree: SceneTree

    def __init__(self, document: LocalDocument, output_dir: pathlib.Path):
        self.document = document
        self.output_dir = output_dir
        self.obsidian_markdown = ObsidianMarkdownFile(document)

        self.pdf_page = None
        self.pdf_size_px = None
        self.page_bounds = None

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
        self.pdf_page = self.get_pdf_page(index, page)
        self.pdf_size_px = (
            self.pdf_page.rect.width * PDF_SCALING,
            self.pdf_page.rect.height * PDF_SCALING
        )

        try:
            self.tree = SceneTree.from_document(self.document, page.id)
        except FailedToBuildTree:
            scrybble_warning_tree_failed_to_build.render_as_annotation(self.pdf_page)
            return
        except FileNotFoundError:
            return

        self.page_bounds = self.get_page_bounds()

        # Calculate the PDF Expand / Offsets
        _pdf_sides = (self.pdf_size_px[0] - self.paper_size[0]) / 2
        pdf_expand_left = (-self.page_bounds.left) - _pdf_sides
        pdf_expand_right = (self.page_bounds.right - _pdf_sides - self.paper_size[0])

        pdf_expand_top = -self.page_bounds.top
        pdf_expand_bottom = self.page_bounds.bottom - self.pdf_size_px[1]

        pdf_expand_y = max(0, pdf_expand_top) + max(0, pdf_expand_bottom)
        pdf_expand_x = max(0, pdf_expand_left) + max(0, pdf_expand_right)

        # Set the mediabox and size of the lines
        mediabox = pe.FRect(
            -max(0, pdf_expand_left), -max(0, pdf_expand_bottom),
            # self.page_bounds.left,
            # self.page_bounds.top,
            self.pdf_size_px[0] + pdf_expand_x,
            self.pdf_size_px[1] + pdf_expand_y
        )

        size_rounded = (
            int(mediabox.width + min(0, pdf_expand_left) + min(0, pdf_expand_right)),
            int(mediabox.height + min(0, pdf_expand_top) + min(0, pdf_expand_bottom))
        )

        # DEBUGGING INFO
        # print("\nPAGE BOUNDS (in px):", self.page_bounds,
        #       "\nPAGE BOUNDS (in pt):", self.page_bounds.scale_by(1 / PDF_SCALING),
        #       f"\nPDF EXPAND (in px): l:{pdf_expand_left}, r:{pdf_expand_right}, t:{pdf_expand_top}, b:{pdf_expand_bottom}",
        #       "\nPDF SIZE (in px):", (self.pdf_page.rect.width, self.pdf_page.rect.height),
        #       "\nPDF MEDIABOX (in pt):", self.pdf_page.mediabox,
        #       "\nResizing to (in px):", mediabox,
        #       "\nResizing to (in pt):", rect_to_murect(mediabox, scaling=ScalingTypes.PDF_PTS))

        self.pdf_page.set_mediabox(rect_to_murect(mediabox, scaling=ScalingTypes.PDF_PTS))

        # Add the backdrop for sampling
        self.renderer.config.backdrop_sampling = True
        self.renderer.config.backdrop_align = BACKDROP_ALIGN_TOP_CENTER
        self.renderer.set_backdrop_pymupdf(self.pdf_page, dpi=227)

        # Render the lines
        frame = frame_to_pixmap(
            self.renderer.get_frame_raw(
                int(self.page_bounds.x), int(self.page_bounds.y),
                int(self.page_bounds.width), int(self.page_bounds.height),
                *size_rounded,
            ),
            size_rounded
        )

        # Add the lines to the PDF page
        self.pdf_page.insert_image(
            rect_to_murect(
                pe.FRect(
                    -min(0, pdf_expand_left),
                    -min(0, pdf_expand_top),
                    *size_rounded
                ),
                scaling=ScalingTypes.PDF_PTS
            ),
            pixmap=frame
        )

        # Add PDF Highlighter annotations for glyph ranges
        self.add_highlighter()

    def add_highlighter(self):
        self.renderer.config.use_whitelist = True
        self.renderer.config.enable_pen(PEN_HIGHLIGHTER)
        self.renderer.config.follow_rules_in_json = True
        self.renderer.config.stroker_data_in_json = True
        for layer in self.renderer.layers:
            layer.update_data()
            for info in layer.lines:
                line: LineItem = info.line
                pass
            for info in layer.glyph_ranges:
                glyph: GlyphRangeItem = info.glyph_range
                for rect in glyph.rects:
                    annot = self.pdf_page.add_highlight_annot(
                        rect_to_murect(
                            pe.FRect(rect).move(self.paper_size[0] / 2 - self.page_bounds.left, 0),
                            scaling=ScalingTypes.PDF_PTS
                        )
                    )
                    annot.set_colors(stroke=(
                        glyph.argb_color[1] / 255,
                        glyph.argb_color[2] / 255,
                        glyph.argb_color[3] / 255,
                    ))
                    annot.set_info(content=glyph.text)
                    annot.set_opacity(0)
                    annot.update()

    @property
    def paper_size(self) -> Tuple[int, int]:
        if self.scene_info:
            return self.scene_info.paper_size
        else:
            return RM_SCREEN_SIZE

    def get_page_bounds(self) -> pe.FRect:
        x, y, x2, y2 = 0, 0, 0, 0
        layers = self.renderer.get_layers()

        if layers:
            for layer in layers:
                size_tracker = layer.size_tracker
                print(size_tracker.left, size_tracker.top, size_tracker.right, size_tracker.bottom)
                x = min(x, size_tracker.left)
                y = min(y, size_tracker.top)
                x2 = max(x2, size_tracker.right)
                y2 = max(y2, size_tracker.bottom)
        rect = pe.FRect((x, y, 1, 1))
        rect.size = (x2 - x, y2 - y)
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
        return self.pdf_document[index]

    def load_or_create_pdf(self):
        if self.document.content.file_type in ["pdf", "epub"]:
            file = self.document.file_uuid_map.get(f'{self.document.uuid}.pdf')
            if not file:
                raise FileNotFoundError("Could not find the PDF file for this document")
            pdf_path = self.document.get_file(file.hash)
            source = pymupdf.open(filename=pdf_path, filetype="pdf")

            self.pdf_document = pymupdf.open()

            for i, page in enumerate(self.doc_pages):
                source_page = page.redirect.value if page.redirect else i

                self.pdf_document.insert_pdf(
                    source,
                    from_page=source_page,
                    to_page=source_page,
                )

            source.close()
        else:
            self.pdf_document = pymupdf.open()  # Create a new empty PDF document
            for _ in self.doc_pages:
                self.pdf_document.new_page()  # Add a new blank page
