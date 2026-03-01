import logging
import struct
from dataclasses import dataclass
from typing import List, TypedDict, Tuple

from rmc.exporters.svg import rmc_config
from rmscene import read_blocks, SceneTree, build_tree, RootTextBlock
from rmscene.scene_items import Line, GlyphRange, Rectangle
from rmscene.text import TextDocument

from ..dimensions import ReMarkableDimensions
from ..metadata import ReMarkableAnnotationsFileHeaderVersion
from ..utils import (
    RM_WIDTH,
    RM_HEIGHT,
)


def update_boundaries_from_point(x, y, boundaries):
    boundaries["x_max"] = max(boundaries["x_max"], x)
    boundaries["y_max"] = max(boundaries["y_max"], y)
    boundaries["x_min"] = min(boundaries["x_min"], x)
    boundaries["y_min"] = min(boundaries["y_min"], y)


@dataclass
class RemarksRectangle:
    color: int
    rectangles: List[Rectangle]


class TTextBlock(TypedDict):
    pos_x: float
    pos_y: float
    width: float
    text: TextDocument


class TMetaData(TypedDict):
    glyph_ranges: List[GlyphRange]
    highlights: List[RemarksRectangle]
    text: TTextBlock | None
    scene_tree: SceneTree | None


def parse_v6(file_path: str) -> Tuple[TMetaData, bool]:
    output: TMetaData = {
        "highlights": [],
        "glyph_ranges": [],
        "text": None,
        "scene_tree": None
    }

    with open(file_path, "rb") as f:
        tree = SceneTree()
        blocks = [b for b in read_blocks(f)]
        build_tree(tree, blocks)

        output["scene_tree"] = tree

        try:
            for block in blocks:
                if isinstance(block, RootTextBlock):
                    output["text"] = {
                        "pos_x": block.value.pos_x,
                        "pos_y": block.value.pos_y,
                        "width": block.value.width,
                        "text": TextDocument.from_scene_item(tree.root_text),
                    }
            for el in tree.walk():
                if isinstance(el, GlyphRange):
                    translated_rectangles = [
                        Rectangle(
                            x=rmc_config.xx(rectangle.x),
                            y=rmc_config.yy(rectangle.y),
                            w=rmc_config.xx(rectangle.w),
                            h=rmc_config.yy(rectangle.h)
                        ) for rectangle in el.rectangles]
                    # sort by reading order
                    translated_rectangles.sort(key=lambda h: (h.y, h.x))
                    highlight: RemarksRectangle = RemarksRectangle(
                        color=el.color.value,
                        rectangles=translated_rectangles)
                    output["glyph_ranges"].append(el)
                    output["highlights"].append(highlight)
        except AssertionError:
            print("ReMarkable broken data")

    return output, False


def determine_document_dimensions(file_path) -> ReMarkableDimensions:
    """The ReMarkable has dynamic document size in v6. The dimensions are not available anywhere, so we'll compute
    them from points"""
    # This is the horizontal space you get as defined by ReMarkable.
    # Not coincidentally, this is (RM_HEIGHT - RM_WIDTH)/2
    # Adding two increments, which is the max, you end up with an exactly square aspect ratio
    # hori = (RM_HEIGHT - RM_WIDTH) / 2
    dims = {
        "x_min": -RM_WIDTH / 2,
        "x_max": RM_WIDTH / 2 - 1,
        "y_min": 0,
        "y_max": RM_HEIGHT - 1,
    }
    with open(file_path, "rb") as f:
        blocks = read_blocks(f)
        tree = SceneTree()
        build_tree(tree, blocks)

        try:
            for el in tree.walk():
                if isinstance(el, Line):
                    for p in el.points:
                        update_boundaries_from_point(p.x, p.y, dims)
        except AssertionError:
            print("ReMarkable broken data")

    return ReMarkableDimensions(
        dims["x_max"] - dims["x_min"], dims["y_max"] - dims["y_min"]
    )


def read_rm_file_version(file_path: str) -> str:
    with open(file_path, "rb") as f:
        src_header = f.readline()

        # 32nd character (marked with V) is the version number
        #                                                       V
        expected_header_fmt = b"reMarkable .lines file, version=0          "
        fmt = f"<{len(expected_header_fmt)}sI"
        header, nlayers = struct.unpack_from(fmt, src_header, 0)
        # 32nd character is the version number
        version = chr(header[32])

        if version == "3":
            return ReMarkableAnnotationsFileHeaderVersion.V3
        elif version == "6":
            return ReMarkableAnnotationsFileHeaderVersion.V6
        else:
            return ReMarkableAnnotationsFileHeaderVersion.UNKNOWN


def check_rm_file_version(file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    expected_header_fmt = b"reMarkable .lines file, version=0          "

    if len(data) < len(expected_header_fmt) + 4:
        logging.error(f"- .rm file ({file_path}) seems too short to be valid")
        return False

    offset = 0
    fmt = f"<{len(expected_header_fmt)}sI"

    header, nlayers = struct.unpack_from(fmt, data, offset)

    is_v3 = header == b"reMarkable .lines file, version=3          "
    is_v5 = header == b"reMarkable .lines file, version=5          "
    is_v6 = header == b"reMarkable .lines file, version=6          "

    if is_v6:
        return True

    if (not is_v3 and not is_v5) or nlayers < 1:
        logging.error(
            f"- .rm file ({file_path}) doesn't look like a valid one: <header={header}><nlayers={nlayers}>"
        )
        return False

    return True


def parse_rm_file(file_path: str) -> Tuple[Tuple[TMetaData, bool], str]:
    with open(file_path, "rb") as f:
        data = f.read()

    expected_header_fmt = b"reMarkable .lines file, version=0          "

    expected_header_v3 = b"reMarkable .lines file, version=3          "
    expected_header_v5 = b"reMarkable .lines file, version=5          "
    expected_header_v6 = b"reMarkable .lines file, version=6          "
    if len(data) < len(expected_header_v5) + 4:
        raise ValueError(f"{file_path} is too short to be a valid .rm file")

    offset = 0
    fmt = f"<{len(expected_header_fmt)}sI"

    header, nlayers = struct.unpack_from(fmt, data, offset)

    offset += struct.calcsize(fmt)

    is_v3 = header == expected_header_v3
    is_v5 = header == expected_header_v5
    is_v6 = header == expected_header_v6

    if is_v6:
        return parse_v6(file_path), "V6"

    raise ValueError(
        f"{file_path} is not a valid .rm file: <header={header}><nlayers={nlayers}>"
    )

# The line segment will pop up hundreds or thousands of times in notebooks where it is relevant.
# this flag ensures it will print at most once.
_line_segment_warning_has_been_shown = False
