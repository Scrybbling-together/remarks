# TODO: Refactor into standalone file that handles
#       all PDF rendering logic
from typing import List

import fitz
from fitz import Page, Rect

from remarks.conversion.parsing import TRemarksRectangle


def apply_smart_highlights(page: Page, highlights: List[TRemarksRectangle],  x_translation: float) -> None:
    for highlight in highlights:
        for rectangle in highlight.rectangles:
            x, y, w, h = rectangle.x, rectangle.y, rectangle.w, rectangle.h
            # compute the width of a blank page that can contain both svg and background pdf
            annot = page.add_highlight_annot(quads=Rect((x+x_translation,y), (x+x_translation+w, y+h)))
            # Current colour taken from RMC's highlight colour, we should support more colours in the future.
            annot.set_colors(stroke=(247 / 255, 232 / 255, 81 / 255))
            annot.set_opacity(0.3)
            annot.update()


def add_error_annotation(page: Page, more_info=""):
    page.add_freetext_annot(
        rect=fitz.Rect(10, 10, 300, 30),
        text="Scrybble error" + more_info,
        fontsize=11,
        text_color=(0, 0, 0),
        fill_color=(1, 1, 1)
    )
