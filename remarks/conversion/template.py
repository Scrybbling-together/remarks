"""
Template rendering for reMarkable .template files.

This module provides functionality to render reMarkable template files
to SVG format for compositing with annotations.
"""

import json
import logging
import re
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_logger = logging.getLogger(__name__)

# Default dimensions (RMPP)
DEFAULT_WIDTH = 1620
DEFAULT_HEIGHT = 2160


class ExpressionEvaluator:
    """
    Evaluates template expressions with support for:
    - Arithmetic: +, -, *, /
    - Comparisons: >, <, >=, <=, ==, !=
    - Ternary: condition ? valueIfTrue : valueIfFalse
    - Logical OR: ||
    - Variable substitution
    """

    def __init__(self, constants: Dict[str, float]):
        self.constants = constants

    def evaluate(self, expr: Union[str, int, float]) -> float:
        """Evaluate an expression and return a numeric value."""
        if isinstance(expr, (int, float)):
            return float(expr)

        if not isinstance(expr, str):
            return 0.0

        expr = expr.strip()

        # Handle ternary operator first (lowest precedence)
        if '?' in expr and ':' in expr:
            return self._eval_ternary(expr)

        # Handle logical OR
        if '||' in expr:
            return self._eval_or(expr)

        # Handle comparisons
        for op in ['>=', '<=', '==', '!=', '>', '<']:
            if op in expr:
                return self._eval_comparison(expr, op)

        # Handle arithmetic
        return self._eval_arithmetic(expr)

    def _eval_ternary(self, expr: str) -> float:
        """Evaluate ternary expression: condition ? valueIfTrue : valueIfFalse"""
        # Find the ? and : positions, handling nested ternaries
        depth = 0
        q_pos = -1
        c_pos = -1

        for i, ch in enumerate(expr):
            if ch == '?':
                if depth == 0 and q_pos == -1:
                    q_pos = i
                depth += 1
            elif ch == ':':
                depth -= 1
                if depth == 0 and c_pos == -1:
                    c_pos = i
                    break

        if q_pos == -1 or c_pos == -1:
            return self._eval_arithmetic(expr)

        condition = expr[:q_pos].strip()
        if_true = expr[q_pos + 1:c_pos].strip()
        if_false = expr[c_pos + 1:].strip()

        cond_result = self.evaluate(condition)
        if cond_result:
            return self.evaluate(if_true)
        else:
            return self.evaluate(if_false)

    def _eval_or(self, expr: str) -> float:
        """Evaluate logical OR expression."""
        parts = expr.split('||')
        for part in parts:
            result = self.evaluate(part.strip())
            if result:
                return result
        return 0.0

    def _eval_comparison(self, expr: str, op: str) -> float:
        """Evaluate comparison expression."""
        parts = expr.split(op, 1)
        if len(parts) != 2:
            return 0.0

        left = self.evaluate(parts[0].strip())
        right = self.evaluate(parts[1].strip())

        if op == '>':
            return 1.0 if left > right else 0.0
        elif op == '<':
            return 1.0 if left < right else 0.0
        elif op == '>=':
            return 1.0 if left >= right else 0.0
        elif op == '<=':
            return 1.0 if left <= right else 0.0
        elif op == '==':
            return 1.0 if left == right else 0.0
        elif op == '!=':
            return 1.0 if left != right else 0.0
        return 0.0

    def _eval_arithmetic(self, expr: str) -> float:
        """Evaluate arithmetic expression with +, -, *, /"""
        expr = expr.strip()

        # Handle parentheses first
        while '(' in expr:
            start = expr.rfind('(')
            end = expr.find(')', start)
            if end == -1:
                break
            inner = expr[start + 1:end]
            result = self._eval_arithmetic(inner)
            expr = expr[:start] + str(result) + expr[end + 1:]

        # Handle addition and subtraction (left to right, lower precedence)
        # But be careful with negative numbers
        tokens = self._tokenize(expr)

        # First pass: handle * and /
        i = 0
        while i < len(tokens):
            if tokens[i] in ['*', '/']:
                left = float(tokens[i - 1])
                right = float(tokens[i + 1])
                if tokens[i] == '*':
                    result = left * right
                else:
                    result = left / right if right != 0 else 0
                tokens = tokens[:i - 1] + [str(result)] + tokens[i + 2:]
            else:
                i += 1

        # Second pass: handle + and -
        if not tokens:
            return 0.0

        result = float(tokens[0])
        i = 1
        while i < len(tokens):
            if tokens[i] == '+':
                result += float(tokens[i + 1])
                i += 2
            elif tokens[i] == '-':
                result -= float(tokens[i + 1])
                i += 2
            else:
                i += 1

        return result

    def _tokenize(self, expr: str) -> List[str]:
        """Tokenize an arithmetic expression, handling variables."""
        import re

        # Split on operators while keeping them
        # This regex splits on +, -, *, / but keeps them as separate tokens
        # It also handles negative numbers at the start or after an operator

        tokens = []
        current = ''
        expr = expr.strip()
        i = 0

        while i < len(expr):
            ch = expr[i]

            if ch.isspace():
                if current:
                    tokens.append(self._resolve_token(current))
                    current = ''
                i += 1
                continue

            if ch in '+-*/':
                if current:
                    # We have accumulated something, emit it
                    tokens.append(self._resolve_token(current))
                    current = ''
                    # Now emit the operator
                    tokens.append(ch)
                else:
                    # No current token - check if this is unary minus
                    if ch == '-' and (not tokens or tokens[-1] in '+-*/'):
                        # Unary minus - start of negative number
                        current = '-'
                    else:
                        # Binary operator
                        tokens.append(ch)
            else:
                current += ch

            i += 1

        if current:
            tokens.append(self._resolve_token(current))

        return tokens

    def _resolve_token(self, token: str) -> str:
        """Resolve a token - either a number or a variable name."""
        token = token.strip()

        # Handle empty token or just operators
        if not token or token in '+-*/':
            return '0'

        # Check if it's a number
        try:
            float(token)
            return token
        except ValueError:
            pass

        # It's a variable - look it up
        if token in self.constants:
            return str(self.constants[token])

        _logger.warning(f"Unknown variable: {token}")
        return '0'


class TemplateRenderer:
    """
    Renders reMarkable templates to SVG format.
    """

    def __init__(self, template_width: int = DEFAULT_WIDTH,
                 template_height: int = DEFAULT_HEIGHT,
                 device: str = "RMPP"):
        self.template_width = template_width
        self.template_height = template_height
        self.device = device
        self.constants: Dict[str, float] = {}
        self.output = StringIO()
        # Offset to apply to x coordinates (for coordinate system alignment)
        self.x_offset = 0
        # Render bounds - the area that needs to be covered with template
        # These are in template coordinates (left-origin)
        # If not set, defaults to template dimensions
        self.render_x_min = 0
        self.render_x_max = template_width
        self.render_y_min = 0
        self.render_y_max = template_height

    def render(self, template_data: Dict[str, Any]) -> str:
        """
        Render a template to SVG content.

        Args:
            template_data: Parsed template JSON

        Returns:
            SVG content as string
        """
        self.output = StringIO()

        # Initialize built-in variables
        # paperOriginX is a reference point for grid alignment
        # Value of 773 was empirically determined to match official reMarkable output
        # (accounts for the scale factor difference between DPI-based and page-fit scaling)
        self.constants = {
            'templateWidth': float(self.template_width),
            'templateHeight': float(self.template_height),
            'paperOriginX': 773.0,
        }

        # Process constants
        if 'constants' in template_data:
            self._process_constants(template_data['constants'])

        # Render items
        items = template_data.get('items', [])
        for item in items:
            self._render_item(item)

        return self.output.getvalue()

    def render_to_svg_group(self, template_data: Dict[str, Any],
                            scale: float = 1.0,
                            stroke_color: str = "#c0c0c0") -> str:
        """
        Render template as an SVG group element suitable for embedding.

        Args:
            template_data: Parsed template JSON
            scale: Scale factor for coordinates
            stroke_color: Default stroke color for paths

        Returns:
            SVG group element as string
        """
        self.output = StringIO()
        self.scale = scale
        self.default_stroke_color = stroke_color

        # Initialize built-in variables
        # paperOriginX is a reference point for grid alignment
        # Value of 773 was empirically determined to match official reMarkable output
        # (accounts for the scale factor difference between DPI-based and page-fit scaling)
        self.constants = {
            'templateWidth': float(self.template_width),
            'templateHeight': float(self.template_height),
            'paperOriginX': 773.0,
        }

        # Process constants
        if 'constants' in template_data:
            self._process_constants(template_data['constants'])

        self.output.write(f'\t<g id="template" opacity="1.0">\n')

        # Render items
        items = template_data.get('items', [])
        for item in items:
            self._render_item(item)

        self.output.write('\t</g>\n')

        return self.output.getvalue()

    def _process_constants(self, constants: List[Dict[str, Any]]):
        """Process template constants, evaluating expressions in order."""
        evaluator = ExpressionEvaluator(self.constants)

        for const_def in constants:
            for name, expr in const_def.items():
                value = evaluator.evaluate(expr)
                self.constants[name] = value
                evaluator.constants[name] = value

    def _eval(self, expr: Union[str, int, float],
              parent_vars: Dict[str, float] = None) -> float:
        """Evaluate an expression with current constants and optional parent vars."""
        combined = dict(self.constants)
        if parent_vars:
            combined.update(parent_vars)
        evaluator = ExpressionEvaluator(combined)
        return evaluator.evaluate(expr)

    def _render_item(self, item: Dict[str, Any],
                     parent_vars: Dict[str, float] = None,
                     transform_x: float = 0,
                     transform_y: float = 0):
        """Render a single item (path, group, or text)."""
        item_type = item.get('type', '')

        if item_type == 'path':
            self._render_path(item, parent_vars, transform_x, transform_y)
        elif item_type == 'group':
            self._render_group(item, parent_vars, transform_x, transform_y)
        elif item_type == 'text':
            self._render_text(item, parent_vars, transform_x, transform_y)
        else:
            _logger.warning(f"Unknown item type: {item_type}")

    def _scale_coord(self, value: float) -> float:
        """Scale a coordinate value."""
        return value * getattr(self, 'scale', 1.0)

    def _scale_x(self, value: float) -> float:
        """Scale an X coordinate value, applying x_offset for coordinate system alignment."""
        return (value + self.x_offset) * getattr(self, 'scale', 1.0)

    def _scale_y(self, value: float) -> float:
        """Scale a Y coordinate value."""
        return value * getattr(self, 'scale', 1.0)

    def _render_path(self, item: Dict[str, Any],
                     parent_vars: Dict[str, float] = None,
                     transform_x: float = 0,
                     transform_y: float = 0):
        """Render a path item to SVG."""
        data = item.get('data', [])
        if not data:
            return

        path_data = self._build_path_data(data, parent_vars, transform_x, transform_y)

        stroke_width = self._eval(item.get('strokeWidth', 1), parent_vars)

        # Get fill color - preserve custom fill colors as-is
        item_fill = item.get('fillColor')
        if item_fill and item_fill.lower() not in ('none', '#00000000'):
            fill_color = item_fill
        else:
            fill_color = 'none'

        # Get stroke color logic:
        # 1. If strokeColor explicitly specified -> use it (custom color)
        # 2. If fillColor specified -> match stroke to fill (for solid shapes)
        # 3. Otherwise -> use light gray (template grid lines)
        item_stroke = item.get('strokeColor')
        if item_stroke is not None:
            # Explicit strokeColor - use it directly
            stroke_color = item_stroke
        elif fill_color != 'none':
            # Has fill but no stroke specified - match stroke to fill
            stroke_color = fill_color
        else:
            # No fill, no stroke - use default light gray for template lines
            stroke_color = getattr(self, 'default_stroke_color', '#c0c0c0')

        self.output.write(
            f'\t\t<path d="{path_data}" stroke="{stroke_color}" '
            f'stroke-width="{self._scale_coord(stroke_width)}" fill="{fill_color}"/>\n'
        )

    def _build_path_data(self, data: List,
                         parent_vars: Dict[str, float] = None,
                         transform_x: float = 0,
                         transform_y: float = 0) -> str:
        """Build SVG path data string from template path commands."""
        result = []
        i = 0

        while i < len(data):
            cmd = data[i]

            if cmd == 'M':
                # Move to: M x y
                x = self._eval(data[i + 1], parent_vars) + transform_x
                y = self._eval(data[i + 2], parent_vars) + transform_y
                result.append(f'M {self._scale_x(x):.2f} {self._scale_y(y):.2f}')
                i += 3
            elif cmd == 'L':
                # Line to: L x y
                x = self._eval(data[i + 1], parent_vars) + transform_x
                y = self._eval(data[i + 2], parent_vars) + transform_y
                result.append(f'L {self._scale_x(x):.2f} {self._scale_y(y):.2f}')
                i += 3
            elif cmd == 'C':
                # Cubic Bezier: C x1 y1 x2 y2 x y
                x1 = self._eval(data[i + 1], parent_vars) + transform_x
                y1 = self._eval(data[i + 2], parent_vars) + transform_y
                x2 = self._eval(data[i + 3], parent_vars) + transform_x
                y2 = self._eval(data[i + 4], parent_vars) + transform_y
                x = self._eval(data[i + 5], parent_vars) + transform_x
                y = self._eval(data[i + 6], parent_vars) + transform_y
                result.append(
                    f'C {self._scale_x(x1):.2f} {self._scale_y(y1):.2f} '
                    f'{self._scale_x(x2):.2f} {self._scale_y(y2):.2f} '
                    f'{self._scale_x(x):.2f} {self._scale_y(y):.2f}'
                )
                i += 7
            elif cmd == 'Z':
                # Close path
                result.append('Z')
                i += 1
            else:
                _logger.warning(f"Unknown path command: {cmd}")
                i += 1

        return ' '.join(result)

    def _render_group(self, item: Dict[str, Any],
                      parent_vars: Dict[str, float] = None,
                      transform_x: float = 0,
                      transform_y: float = 0):
        """Render a group item, handling repeat expansion."""
        bbox = item.get('boundingBox', {})
        repeat = item.get('repeat', {})
        children = item.get('children', [])

        # Evaluate bounding box
        box_x = self._eval(bbox.get('x', 0), parent_vars)
        box_y = self._eval(bbox.get('y', 0), parent_vars)
        box_w = self._eval(bbox.get('width', 100), parent_vars)
        box_h = self._eval(bbox.get('height', 100), parent_vars)

        # Determine repeat counts and starting positions
        cols = repeat.get('columns', 1)
        rows = repeat.get('rows', 1)

        col_count, start_x = self._resolve_repeat_count(cols, box_x, box_w, 'x')
        row_count, start_y = self._resolve_repeat_count(rows, box_y, box_h, 'y')

        # Create group variables
        group_vars = dict(parent_vars) if parent_vars else {}
        group_vars['groupWidth'] = box_w
        group_vars['groupHeight'] = box_h
        # parentWidth/parentHeight are aliases used in child items
        group_vars['parentWidth'] = box_w
        group_vars['parentHeight'] = box_h

        # Render repeated instances
        for row in range(row_count):
            for col in range(col_count):
                # Calculate position using adjusted start positions for infinite tiling
                inst_x = start_x + col * box_w
                inst_y = start_y + row * box_h

                # Update instance variables
                inst_vars = dict(group_vars)
                inst_vars['colIndex'] = col
                inst_vars['rowIndex'] = row

                # Render children at this position
                for child in children:
                    self._render_item(
                        child, inst_vars,
                        transform_x + inst_x,
                        transform_y + inst_y
                    )

    def _resolve_repeat_count(self, value: Union[str, int],
                              start: float, size: float,
                              axis: str) -> tuple:
        """
        Resolve repeat count value.

        Returns:
            Tuple of (count, start_position) where start_position is the
            adjusted starting position for infinite tiling.
        """
        if isinstance(value, int):
            return (value, start)

        if value == 'infinite':
            # Calculate how many fit in the render area (which may extend beyond template)
            if axis == 'x':
                # For infinite columns, tile to cover full render width
                # Use render bounds instead of template dimensions
                x_start = min(self.render_x_min, 0)
                x_end = max(self.render_x_max, self.template_width)
                xpos = start
                if size > 0:
                    # Find first tile position that's before x_start
                    first_pos = xpos % size
                    if first_pos > 0:
                        first_pos -= size
                    # Go back further if needed to cover render_x_min
                    while first_pos > x_start:
                        first_pos -= size
                    # Count tiles needed to cover from first_pos to x_end
                    count = int((x_end - first_pos) / size) + 2
                    return (count, first_pos)
                return (1, start)
            else:
                # For infinite rows, tile to cover full render height
                y_start = min(self.render_y_min, 0)
                y_end = max(self.render_y_max, self.template_height)
                ypos = start
                if size > 0:
                    first_pos = ypos % size
                    if first_pos > 0:
                        first_pos -= size
                    while first_pos > y_start:
                        first_pos -= size
                    count = int((y_end - first_pos) / size) + 2
                    return (count, first_pos)
                return (1, start)

        if value == 'down':
            # Repeat downward to fill remaining height (use render bounds)
            y_end = max(self.render_y_max, self.template_height)
            remaining = y_end - start
            if size > 0:
                return (max(1, int(remaining / size) + 1), start)
            return (1, start)

        if value == 'up':
            # Repeat upward from start
            if size > 0:
                return (max(1, int(start / size) + 1), start)
            return (1, start)

        if value == 'right':
            # Repeat rightward to fill remaining width (use render bounds)
            x_end = max(self.render_x_max, self.template_width)
            remaining = x_end - start
            if size > 0:
                return (max(1, int(remaining / size) + 1), start)
            return (1, start)

        # Try to evaluate as expression
        try:
            return (int(self._eval(value)), start)
        except:
            return (1, start)

    def _render_text(self, item: Dict[str, Any],
                     parent_vars: Dict[str, float] = None,
                     transform_x: float = 0,
                     transform_y: float = 0):
        """Render a text item to SVG."""
        text = item.get('text', '')
        font_size = item.get('fontSize', 12)
        position = item.get('position', {})

        # Estimate text width for textWidth variable
        # Rough approximation: average character is ~0.6 * font_size
        text_width = len(text) * font_size * 0.6

        # Add textWidth to variables for position evaluation
        text_vars = dict(parent_vars) if parent_vars else {}
        text_vars['textWidth'] = text_width

        # Evaluate position
        x = self._eval(position.get('x', 0), text_vars) + transform_x
        y = self._eval(position.get('y', 0), text_vars) + transform_y

        # Escape text for XML
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        self.output.write(
            f'\t\t<text x="{self._scale_x(x):.2f}" y="{self._scale_y(y):.2f}" '
            f'font-size="{self._scale_coord(font_size):.2f}" '
            f'fill="#000000">'
            f'{escaped_text}</text>\n'
        )


def get_bundled_templates_dir() -> Path:
    """Return the path to bundled template files."""
    return Path(__file__).parent.parent / "assets" / "templates"


def load_template(template_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a template file and return parsed JSON data.

    Args:
        template_path: Path to .template file

    Returns:
        Parsed template data or None if not found
    """
    if not template_path.exists():
        _logger.warning(f"Template file not found: {template_path}")
        return None

    try:
        with open(template_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        _logger.error(f"Failed to parse template {template_path}: {e}")
        return None


def load_template_by_name(templates_dir: Path, name: str) -> Optional[Dict[str, Any]]:
    """
    Load a template by name from a templates directory.

    Args:
        templates_dir: Directory containing .template files
        name: Template name (with or without .template extension)

    Returns:
        Parsed template data or None if not found
    """
    # Normalize name
    if not name.endswith('.template'):
        name = f"{name}.template"

    template_path = templates_dir / name
    return load_template(template_path)


def get_template_for_page(content_data: Dict[str, Any],
                          page_uuid: str) -> Optional[str]:
    """
    Get the template name for a specific page from .content data.

    Args:
        content_data: Parsed .content file data
        page_uuid: UUID of the page

    Returns:
        Template name or None if no template assigned
    """
    # Check cPages format (newer)
    if 'cPages' in content_data:
        for page in content_data['cPages'].get('pages', []):
            if page.get('id') == page_uuid:
                template = page.get('template', {})
                if isinstance(template, dict):
                    return template.get('value')
                return template if template else None

    # Check pages format with pageTemplates (older)
    if 'pageTemplates' in content_data:
        try:
            page_idx = content_data.get('pages', []).index(page_uuid)
            templates = content_data['pageTemplates']
            if page_idx < len(templates):
                return templates[page_idx] if templates[page_idx] else None
        except (ValueError, IndexError):
            pass

    return None


def render_template_to_svg_group(template_data: Dict[str, Any],
                                  screen_width: int,
                                  screen_height: int,
                                  scale: float,
                                  stroke_color: str = "#c0c0c0") -> str:
    """
    Render a template as an SVG group element.

    Args:
        template_data: Parsed template JSON data
        screen_width: Device screen width in pixels
        screen_height: Device screen height in pixels
        scale: Scale factor for output coordinates
        stroke_color: Stroke color for template elements

    Returns:
        SVG group element as string
    """
    renderer = TemplateRenderer(screen_width, screen_height)
    # Apply x_offset to center the template coordinates with content
    renderer.x_offset = -screen_width / 2
    return renderer.render_to_svg_group(template_data, scale, stroke_color)
