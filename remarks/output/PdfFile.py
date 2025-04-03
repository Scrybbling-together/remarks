# TODO: Refactor into standalone file that handles
#       all PDF rendering logic

import fitz
from fitz import Page, Rect, Annot, Quad

from remarks.conversion.parsing import RemarksRectangle
from remarks.warnings import scrybble_warning_typed_text_highlighting_not_supported


def apply_smart_highlight(page: Page, highlight: RemarksRectangle, x_translation: float) -> None:
    for rectangle in highlight.rectangles:
        x, y, w, h = rectangle.x, rectangle.y, rectangle.w, rectangle.h
        # compute the width of a blank page that can contain both svg and background pdf
        annot: Annot = page.add_highlight_annot(quads=Rect((x+x_translation,y), (x+x_translation+w, y+h)))
        # Current colour taken from RMC's highlight colour, we should support more colours in the future.
        annot.set_colors(stroke=(247 / 255, 232 / 255, 81 / 255))
        annot.set_opacity(0.3)
        annot.update()

        words_on_page = page.get_textpage().extractWORDS()
        highlighted_text = extract_annot(annot, words_on_page)

        if not highlighted_text:
            page.delete_annot(annot)
            scrybble_warning_typed_text_highlighting_not_supported.render_as_annotation(page)

def add_error_annotation(page: Page, more_info=""):
    page.add_text_annot(
        text="Scrybble error" + more_info,
        icon="Note",
        point=(10, 10)
    )


# Following two functions are lifted almost directly from https://github.com/pymupdf/PyMuPDF/issues/318#issuecomment-658781494.

def check_contain(r_word, points):
    """If `r_word` is contained in the rectangular area.

    The area of the intersection should be large enough compared to the
    area of the given word.

    Args:
        r_word (fitz.Rect): rectangular area of a single word.
        points (list): list of points in the rectangular area of the
            given part of a highlight.

    Returns:
        bool: whether `r_word` is contained in the rectangular area.
    """
    # `r` is mutable, so everytime a new `r` should be initiated.
    r = Quad(points).rect
    r.intersect(r_word)

    return r.get_area() >= r_word.get_area() * 0.5


def extract_annot(annot, words_on_page):
    """Extract words in a given highlight.

    Args:
        annot (fitz.Annot): [description]
        words_on_page (list): [description]

    Returns:
        str: words in the entire highlight.
    """
    quad_points = annot.vertices
    quad_count = int(len(quad_points) / 4)
    sentences = ['' for i in range(quad_count)]
    for i in range(quad_count):
        points = quad_points[i * 4: i * 4 + 4]
        words = [
            w for w in words_on_page if
            check_contain(Rect(w[:4]), points)
        ]
        sentences[i] = ' '.join(w[4] for w in words)
    sentence = ' '.join(sentences)

    return sentence
