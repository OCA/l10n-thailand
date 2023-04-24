# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportTaxReportXlsx(models.TransientModel):
    _name = "report.l10n_th_account_tax_report.report_tax_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Tax Report Excel"

    def _define_formats(self, workbook):
        res = super()._define_formats(workbook)
        date_format = "DD/MM/YYYY"
        FORMATS["format_date_dmy_right"] = workbook.add_format(
            {"align": "right", "num_format": date_format}
        )
        return res

    def _get_tax_template(self):
        return {
            "1_index": {
                "header": {"value": "#"},
                "data": {"value": self._render("index")},
                "width": 3,
            },
            "2_tax_date": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("tax_date"),
                    "type": "datetime",
                    "format": FORMATS["format_date_dmy_right"],
                },
                "width": 12,
            },
            "3_tax_invoice": {
                "header": {"value": "Number"},
                "data": {"value": self._render("tax_invoice_number")},
                "width": 18,
            },
            "4_partner_name": {
                "header": {"value": "Cust./Sup."},
                "data": {"value": self._render("partner_name")},
                "width": 30,
            },
            "5_partner_vat": {
                "header": {"value": "Tax ID"},
                "data": {"value": self._render("partner_vat")},
                "width": 15,
            },
            "6_partner_branch": {
                "header": {"value": "Branch ID"},
                "data": {"value": self._render("partner_branch")},
                "width": 12,
            },
            "7_tax_base_amount": {
                "header": {"value": "Base Amount"},
                "data": {
                    "value": self._render("tax_base_amount"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 21,
            },
            "8_tax_amount": {
                "header": {"value": "Tax Amount"},
                "data": {
                    "value": self._render("tax_amount"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 21,
            },
            "9_doc_ref": {
                "header": {"value": "Doc Ref."},
                "data": {"value": self._render("doc_ref")},
                "width": 18,
            },
        }

    def _get_ws_params(self, wb, data, objects):
        tax_template = self._get_tax_template()
        ws_params = {
            "ws_name": "TAX Report",
            "generate_ws_method": "_vat_report",
            "title": "TAX Report",
            "wanted_list": [k for k in sorted(tax_template.keys())],
            "col_specs": tax_template,
        }
        if objects.tax_id.type_tax_use == "sale":
            ws_params["ws_name"] = "Sale TAX Report"
            ws_params["title"] = "Sale TAX Report"
        elif objects.tax_id.type_tax_use == "purchase":
            ws_params["ws_name"] = "Purchase TAX Report"
            ws_params["title"] = "Purchase TAX Report"

        return [ws_params]

    def _write_ws_header(self, row_pos, ws, data_list):
        for data in data_list:
            ws.merge_range(row_pos, 0, row_pos, 2, "")
            ws.write_row(row_pos, 0, [data[0]], FORMATS["format_theader_blue_center"])
            ws.merge_range(row_pos, 3, row_pos, 5, "")
            ws.write_row(row_pos, 2, [data[1]], FORMATS["format_tcell_left"])
            row_pos += 1
        return row_pos + 1

    def _get_render_space(self, index, line):
        return {
            "index": index,
            "tax_date": line.tax_date or "",
            "tax_invoice_number": line.tax_invoice_number or "",
            "partner_name": line.partner_id.display_name or "",
            "partner_vat": line.partner_id.vat or "",
            "partner_branch": line.partner_id.branch or "",
            "tax_base_amount": line.tax_base_amount or 0.00,
            "tax_amount": line.tax_amount or 0.00,
            "doc_ref": line.name or "",
        }

    def _write_ws_lines(self, row_pos, ws, ws_params, objects):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_left"],
        )
        ws.freeze_panes(row_pos, 0)
        index = 1
        for line in objects.results:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._get_render_space(index, line),
                default_format=FORMATS["format_tcell_left"],
            )
            index += 1
        return row_pos

    def _write_ws_footer(self, row_pos, ws, ws_params, objects):
        results = objects.results
        col_end = ws_params["wanted_list"].index("7_tax_base_amount")
        ws.merge_range(row_pos, 0, row_pos, col_end - 1, "")
        ws.write_row(
            row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
        )
        ws.write_row(
            row_pos,
            col_end,
            [
                sum(results.mapped("tax_base_amount")),
                sum(results.mapped("tax_amount")),
                "",
            ],
            FORMATS["format_theader_blue_amount_right"],
        )
        return row_pos

    def _vat_report(self, wb, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        row_pos = 0
        header_data_list = self._get_header_data_list(objects)
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        row_pos = self._write_ws_header(row_pos, ws, header_data_list)
        row_pos = self._write_ws_lines(row_pos, ws, ws_params, objects)
        row_pos = self._write_ws_footer(row_pos, ws, ws_params, objects)

    def _get_header_data_list(self, objects):
        return [
            ("Date From", objects.date_from.strftime("%d/%m/%Y") or "-"),
            ("Date To", objects.date_to.strftime("%d/%m/%Y") or "-"),
            ("Company", objects.company_id.display_name or "-"),
            ("Tax ID", objects.company_id.partner_id.vat or "-"),
            ("Company Tax Branch", objects.company_id.partner_id.branch or "-"),
        ]
