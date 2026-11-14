# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from .rd_text import get_text_lines

# Rows of the table of the RD report (px): height of a row on one line, of each
# wrapped line, and of the rows of a page, leaving room for the page total and the
# grand total (15 rows on one line)
RD_ROW_HEIGHT = 36
RD_WRAPPED_LINE_HEIGHT = 30
RD_PAGE_ROWS_HEIGHT = 540
RD_FONT_SIZE = 20
# Columns which can wrap: width of their text (px), as in tax_report_rd.xml
RD_WRAP_COLUMNS = {"tax_invoice_number": 107, "doc_refs": 107, "partner_name": 255}


class RDThaiTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_rd_thai_tax"
    _inherit = "report.l10n_th_account_tax_report.report_thai_tax"
    _description = "Thai Tax Report RD"

    def _get_rd_line_count(self, line):
        """Number of lines of the row, with its texts wrapped in their columns"""
        texts = dict(line, doc_refs=", ".join(ref for ref, _ in line["doc_refs"]))
        return max(
            get_text_lines(texts.get(key), RD_FONT_SIZE, width)
            for key, width in RD_WRAP_COLUMNS.items()
        )

    def _get_rd_pages(self, lines):
        """Split the lines in pages of the height of the form, with their totals"""
        pages, page_lines, height = [], [], 0
        for line in lines:
            line_height = RD_ROW_HEIGHT + RD_WRAPPED_LINE_HEIGHT * (
                self._get_rd_line_count(line) - 1
            )
            if page_lines and height + line_height > RD_PAGE_ROWS_HEIGHT:
                pages.append(page_lines)
                page_lines, height = [], 0
            page_lines.append(line)
            height += line_height
        if page_lines:
            pages.append(page_lines)
        return [
            {
                "lines": page_lines,
                "total_base": sum(line["tax_base_amount"] for line in page_lines),
                "total_tax": sum(line["tax_amount"] for line in page_lines),
            }
            for page_lines in pages
        ]

    def _get_report_values(self, docids, data):
        report_values = super()._get_report_values(docids, data)

        data = report_values["docs"]._prepare_report_tax()

        company = self.env["res.company"].browse(data["company_id"])
        report_values["company_address"] = company.partner_id._display_address(
            without_name=True
        )
        report_values["rd_pages"] = self._get_rd_pages(report_values["tax_report_data"])
        return report_values
