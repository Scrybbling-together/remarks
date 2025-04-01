from rmscene.scene_items import GlyphRange, Rectangle, PenColor

from remarks.output.ObsidianMarkdownFile import merge_highlights


def test_merge_highlights_where_start_is_missing():
    """It is possible for GlyphRanges to have a start of None.
    It is unknown what causes this.

    Hypotheses are:

    1. It is a bug in xochitl
    2. It is a bug in rmscene
    3. It is a problem with PDF, that the start cannot be determined"""
    ranges = [GlyphRange(start=None, length=20, text='types of pens to see', color=PenColor.HIGHLIGHT,
                         rectangles=[Rectangle(x=-144.8671875, y=230.6015625, w=305.328125, h=44.390625)]),
              GlyphRange(start=None, length=23, text='which ones i would take', color=PenColor.HIGHLIGHT,
                         rectangles=[Rectangle(x=202.4765625, y=276.1953125, w=360.578125, h=44.390625)])]

    merge_highlights(ranges)
