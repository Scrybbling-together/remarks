"""
Rendering module for remarks with template support.

This module provides functions to render reMarkable pages with
template backgrounds to SVG and PDF formats.
"""

import logging
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional

from rmscene import read_tree
from rmc.exporters.svg import (
    build_anchor_pos, get_bounding_box,
    xx, yy, SVG_HEADER, draw_text, draw_group,
    SCREEN_WIDTH, SCREEN_HEIGHT, SCALE,
)
from rmc.exporters.pdf import chrome_svg_to_pdf
from cairosvg import svg2pdf

from .template import TemplateRenderer

_logger = logging.getLogger(__name__)

TEMPLATE_LINE_COLOUR = "#c0c0c0"

def render_page_with_template(
    rm_path: Path,
    output_path: Path,
    template_data: Optional[Dict[str, Any]] = None,
    output_format: str = "svg",
    use_chrome: bool = True,
    chrome_loc: Optional[str] = None
) -> bool:
    """
    Render a .rm file to SVG or PDF with optional template background.
    Uses Chrome headless for PDF conversion to ensure proper font embedding.

    Args:
        rm_path: Path to the .rm annotation file
        output_path: Path to save the output file
        template_data: Parsed template JSON data (optional)
        output_format: "svg" or "pdf"

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the scene tree from the .rm file
        with open(rm_path, 'rb') as f:
            tree = read_tree(f)

        # Generate SVG content
        svg_content = render_tree_with_template(tree, template_data)

        if output_format == "svg":
            # Write SVG directly
            with open(output_path, 'w') as f:
                f.write(svg_content)
        elif output_format == "pdf":
            # Write SVG to temp file and convert to PDF
            with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
                f.write(svg_content)
                temp_svg = f.name
            try:
                if use_chrome:
                    chrome_svg_to_pdf(temp_svg, str(output_path), chrome_loc)
                else:
                    svg2pdf(url=temp_svg, write_to=str(output_path), dpi=72)
            finally:
                Path(temp_svg).unlink(missing_ok=True)
        else:
            _logger.error(f"Unknown output format: {output_format}")
            return False

        return True

    except Exception as e:
        _logger.error(f"Failed to render {rm_path}: {e}")
        return False


def render_tree_with_template(
    tree,
    template_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Render a scene tree to SVG with optional template background.

    Args:
        tree: Scene tree from rmscene
        template_data: Parsed template JSON data (optional)

    Returns:
        SVG content as string
    """
    output = StringIO()

    # Build anchor positions for text
    anchor_pos, newline_offsets, anchor_x_pos, anchor_soft_offset = build_anchor_pos(
        tree.root_text, extended=True
    )

    # Get text position
    text_pos_x = tree.root_text.pos_x if tree.root_text is not None else None

    # Get bounding box (in screen coordinates, center-origin)
    x_min, x_max, y_min, y_max = get_bounding_box(
        tree.root, anchor_pos, newline_offsets, text_pos_x, anchor_x_pos, anchor_soft_offset
    )

    width_pt = xx(x_max - x_min + 1)
    height_pt = yy(y_max - y_min + 1)

    # Write SVG header
    output.write(SVG_HEADER.substitute(
        width=width_pt,
        height=height_pt,
        viewbox=f"{xx(x_min)} {yy(y_min)} {width_pt} {height_pt}"
    ) + "\n")

    # Render template background if provided
    if template_data is not None:
        # Pass full bounding box so template tiles to cover all content
        template_svg = render_template_background(
            template_data, x_min, x_max, y_min, y_max
        )
        output.write(template_svg)

    # Render annotations
    output.write(f'\t<g id="p1" style="display:inline">\n')

    if tree.root_text is not None:
        draw_text(tree.root_text, output)

    draw_group(
        tree.root, output, anchor_pos, newline_offsets,
        text_pos_x, anchor_x_pos, anchor_soft_offset
    )

    output.write('\t</g>\n')
    output.write('</svg>\n')

    return output.getvalue()


def render_template_background(
    template_data: Dict[str, Any],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float
) -> str:
    """
    Render template data as an SVG background layer.

    Args:
        template_data: Parsed template JSON data
        x_min, x_max, y_min, y_max: Bounding box in screen coordinates (center-origin)

    Returns:
        SVG group element as string
    """
    # Convert screen coords to template coords (add SCREEN_WIDTH/2 to shift from center to left origin)
    # The bounding box tells us how far the content extends
    template_x_min = x_min + SCREEN_WIDTH / 2
    template_x_max = x_max + SCREEN_WIDTH / 2
    template_y_min = y_min
    template_y_max = y_max

    # Create renderer with dimensions that cover the full bounding box
    # Use at least the standard template size, but expand if content goes beyond
    render_width = max(SCREEN_WIDTH, template_x_max, -template_x_min + SCREEN_WIDTH)
    render_height = max(SCREEN_HEIGHT, template_y_max)

    renderer = TemplateRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
    # Set the actual bounds for tiling
    renderer.render_x_min = template_x_min
    renderer.render_x_max = template_x_max
    renderer.render_y_min = template_y_min
    renderer.render_y_max = template_y_max
    # Apply x_offset to align template coords (left-origin) with content coords (center-origin)
    renderer.x_offset = -SCREEN_WIDTH / 2
    return renderer.render_to_svg_group(template_data, SCALE, TEMPLATE_LINE_COLOUR)


def rm_to_svg_with_template(
    rm_path: Path,
    svg_path: Path,
    template_data: Optional[Dict[str, Any]] = None
):
    """
    Convert .rm file to SVG with optional template background.

    Args:
        rm_path: Path to .rm file
        svg_path: Path to output SVG file
        template_data: Parsed template JSON data (optional)
    """
    with open(rm_path, 'rb') as f:
        tree = read_tree(f)

    svg_content = render_tree_with_template(tree, template_data)

    with open(svg_path, 'w') as f:
        f.write(svg_content)


def rm_to_pdf_with_template(
    rm_path: Path,
    pdf_path: Path,
    template_data: Optional[Dict[str, Any]] = None,
    use_chrome: bool = True,
    chrome_loc: Optional[str] = None
):
    """
    Convert .rm file to PDF with optional template background.
    Uses Chrome headless for proper font embedding.

    Args:
        rm_path: Path to .rm file
        pdf_path: Path to output PDF file
        template_data: Parsed template JSON data (optional)
    """
    with open(rm_path, 'rb') as f:
        tree = read_tree(f)

    svg_content = render_tree_with_template(tree, template_data)

    # Write SVG to temp file and convert to PDF
    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(svg_content)
        temp_svg = f.name

    try:
        if use_chrome:
            chrome_svg_to_pdf(temp_svg, str(pdf_path), chrome_loc)
        else:
            svg2pdf(url=temp_svg, write_to=str(pdf_path), dpi=72)
    finally:
        Path(temp_svg).unlink(missing_ok=True)
