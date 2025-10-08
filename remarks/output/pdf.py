# TODO: Refactor into standalone file that handles
#       all PDF rendering logic

import fitz
from fitz import Page, Rect, Annot, Quad

from remarks.conversion.parsing import RemarksRectangle
from remarks.warnings import scrybble_warning_typed_text_highlighting_not_supported
from rmscene.scene_items import PenColor, HARDCODED_COLORMAP


def get_highlight_color(pen_color: int) -> tuple[float, float, float]:
    """Convert PenColor enum value to RGB tuple for PDF annotations.
    
    Args:
        pen_color: PenColor enum value from rmscene
        
    Returns:
        RGB tuple with values normalized to 0-1 range for PyMuPDF
    """
    # Create reverse mapping from PenColor to RGBA
    color_to_rgba = {v: k for k, v in HARDCODED_COLORMAP.items()}
    
    # Try to convert to PenColor enum, fall back to raw integer lookup
    try:
        pen_color_enum = PenColor(pen_color)
        rgba = color_to_rgba.get(pen_color_enum, (255, 237, 117, 255))
    except ValueError:
        # If the color value is not a valid PenColor enum, use fallback
        rgba = (255, 237, 117, 255)
    
    # Convert to RGB (ignore alpha) and normalize to 0-1 range
    r, g, b, _ = rgba
    return (r / 255, g / 255, b / 255)


def apply_smart_highlight(page: Page, highlight: RemarksRectangle, x_translation: float) -> None:
    # Get the color for this highlight based on its PenColor value
    highlight_color = get_highlight_color(highlight.color)

    for rectangle in highlight.rectangles:
        x, y, w, h = rectangle.x, rectangle.y, rectangle.w, rectangle.h
        # Highlight rectangles are already in PDF coordinate space via xx/yy transformation
        # x_translation positions them correctly relative to reMarkable's (0,0) at center-top of PDF
        annot: Annot = page.add_highlight_annot(quads=Rect((x+x_translation,y), (x+x_translation+w, y+h)))
        # Use the dynamic color based on the highlight's actual color from the reMarkable file
        annot.set_colors(stroke=highlight_color)
        annot.set_opacity(0.3)
        annot.update()


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
