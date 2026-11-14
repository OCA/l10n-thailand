# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Width of the texts printed on the RD forms, with the font of the forms, to
fit long texts (names, addresses) in their boxes."""

import re
import unicodedata
from functools import lru_cache

from PIL import ImageFont

from odoo.tools.misc import file_path

THAI = re.compile("[\u0e00-\u0e7f]")
RD_FONT = "l10n_th_base_utils/static/fonts/thai/THSarabun/THSarabun-Regular.ttf"


@lru_cache(maxsize=8)
def _get_font(size):
    return ImageFont.truetype(file_path(RD_FONT), size)


def get_text_width(text, size):
    """Width in px of the text printed in THSarabun at the font size (px)"""
    return _get_font(size).getlength(text or "")


def get_text_lines(text, size, width):
    """Number of lines of the text wrapped in the width (px): a Thai text breaks
    between its words, about anywhere, other words go to the next line whole"""
    space = get_text_width(" ", size)
    lines, current = 1, 0.0
    for word in (text or "").split():
        word_width = get_text_width(word, size)
        if THAI.search(word):
            current += (space if current else 0) + word_width
            while current > width:
                lines += 1
                # Breaking between words loses the end of the lines
                current -= width * 0.95
        elif current and current + space + word_width > width:
            lines += 1
            current = word_width
        else:
            current += (space if current else 0) + word_width
    return lines


def shorten_text(text, size, width):
    """Start of the text ended by an ellipsis, to fit in the width (px), cut
    before a character which is not a mark of the previous one"""
    ends = [
        end for end in range(1, len(text)) if unicodedata.category(text[end]) != "Mn"
    ]
    low, high = 0, len(ends)
    while low < high:
        middle = (low + high) // 2
        if get_text_width(text[: ends[middle]].rstrip() + "…", size) <= width:
            low = middle + 1
        else:
            high = middle
    return text[: ends[low - 1]].rstrip() + "…" if low else "…"
