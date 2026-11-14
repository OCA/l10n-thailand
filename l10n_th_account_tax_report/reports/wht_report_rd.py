# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from .rd_text import get_text_lines, get_text_width, shorten_text

RD_ROWS_PER_PAGE = {"pnd1": 8, "pnd1a": 7, "pnd2": 7, "pnd3": 6, "pnd53": 6}
# Texts written on the dotted lines of the forms: width (px) and number of the
# dotted lines of each box, as in style_report.scss
RD_TEXT_BOXES = {
    "pnd1": {"partner_firstname": (240, 1), "partner_lastname": (251, 1)},
    "pnd1a": {
        "partner_firstname": (188, 1),
        "partner_lastname": (200, 1),
        "partner_address": (420, 1),
    },
    "pnd2": {"partner_firstname": (160, 1), "partner_lastname": (150, 1)},
    "pnd3": {
        "partner_firstname": (270, 1),
        "partner_lastname": (200, 1),
        "partner_address": (488, 1),
    },
    "pnd53": {"partner_name": (402, 1), "partner_address": (397, 2)},
}
RD_FONT_SIZE = 18
RD_MIN_FONT_SIZE = 12
# Font size to wrap a text on the next dotted line, close to each other
RD_WRAP_FONT_SIZE = 16


class RDWithholdingTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_rd_withholding_tax"
    _inherit = "report.l10n_th_account_tax_report.report_withholding_tax"
    _description = "Thai Withholding Tax Report RD"

    def _get_rd_rows_per_page(self, income_tax_form):
        """Return the row capacity of the RD form."""
        return RD_ROWS_PER_PAGE[income_tax_form]

    def _get_rd_pages(self, lines, rows_per_page, base_key, amount_key):
        """Split RD lines into pages with their totals."""
        pages = []
        for start in range(0, len(lines), rows_per_page):
            page_lines = lines[start : start + rows_per_page]
            pages.append(
                {
                    "lines": page_lines,
                    "total_base": sum((line[base_key] for line in page_lines), 0.0),
                    "total_wht": sum((line[amount_key] for line in page_lines), 0.0),
                }
            )
        return pages

    def _get_rd_text_fit(self, text, width, lines=1):
        """Font size (px) and text to write in a box of the form: smaller for a
        long text, on one line, else wrapped on the next dotted lines if any,
        shortened if too long at the minimum size"""
        text = text or ""
        for size in range(RD_FONT_SIZE, RD_MIN_FONT_SIZE - 1, -1):
            if get_text_width(text, size) <= width:
                return size, text
            wrapped = lines > 1 and size <= RD_WRAP_FONT_SIZE
            if wrapped and get_text_lines(text, size, width) <= lines:
                return size, text
        # Wrapping loses the end of the lines
        width = width * lines * 0.95 if lines > 1 else width
        return RD_MIN_FONT_SIZE, shorten_text(text, RD_MIN_FONT_SIZE, width)

    def _fit_rd_texts(self, line, income_tax_form):
        """Fit the long texts of the line in their boxes of the form: shorten
        them in the line, return the font size of each by key of the line"""
        styles = {}
        for key, (width, lines) in RD_TEXT_BOXES.get(income_tax_form, {}).items():
            if not line.get(key):
                continue
            size, line[key] = self._get_rd_text_fit(line[key], width, lines)
            if size != RD_FONT_SIZE:
                styles[key] = f"font-size: {size}px;"
        return styles

    def _get_report_values(self, docids, data):
        """Add paginated lines and page totals to the RD report values."""
        values = super()._get_report_values(docids, data)
        income_tax_form = values["income_tax_form"]
        if income_tax_form == "pnd1a":
            lines = values["wht_groupby_partner"]
            base_key, amount_key = "total_base", "total_amount"
        else:
            lines = values["wht_report_data"]
            base_key, amount_key = "base", "amount"
        for line in lines:
            line["rd_styles"] = self._fit_rd_texts(line, income_tax_form)
        values["rd_pages"] = self._get_rd_pages(
            lines, self._get_rd_rows_per_page(income_tax_form), base_key, amount_key
        )
        return values
