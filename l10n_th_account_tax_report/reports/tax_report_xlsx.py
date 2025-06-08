# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import models

from odoo.addons.account.models.account_tax import TYPE_TAX_USE
from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportThaiTaxXlsx(models.TransientModel):
    _name = "report.l10n_th_account_tax_report.report_thai_tax_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Tax Report Excel"

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

    def _get_ws_params(self, wb, data, obj):
        tax_template = self._get_tax_template()
        ws_params = {
            "ws_name": "TAX Report",
            "generate_ws_method": "_vat_report",
            "title": "TAX Report",
            "wanted_list": [k for k in sorted(tax_template.keys())],
            "col_specs": tax_template,
        }
        if obj.tax_id.type_tax_use in ["sale", "purchase"]:
            ws_params["ws_name"] = (
                f"{dict(TYPE_TAX_USE).get(obj.tax_id.type_tax_use)} TAX Report"
            )
            ws_params["title"] = (
                f"{dict(TYPE_TAX_USE).get(obj.tax_id.type_tax_use)} TAX Report"
            )
        return [ws_params]

    def _write_ws_header(self, row_pos, ws, data_list):
        for data in data_list:
            ws.merge_range(row_pos, 0, row_pos, 2, "")
            ws.write_row(row_pos, 0, [data[0]], FORMATS["format_theader_blue_center"])
            ws.merge_range(row_pos, 3, row_pos, 5, "")
            ws.write_row(row_pos, 3, [data[1]], FORMATS["format_tcell_left"])
            row_pos += 1
        return row_pos + 1

    def _get_render_space(self, line):
        return {
            "index": line["row_number"],
            "tax_date": line["tax_date"] or "",
            "tax_invoice_number": line["tax_invoice_number"] or "",
            "partner_name": line["partner_name"] or "",
            "partner_vat": line["partner_vat"] or "",
            "partner_branch": line["partner_branch"] or "",
            "tax_base_amount": line["tax_base_amount"] or 0.00,
            "tax_amount": line["tax_amount"] or 0.00,
            "doc_ref": line["name"] or "",
        }

    def _write_ws_lines(self, row_pos, ws, ws_params, tax_report_data):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_left"],
        )
        ws.freeze_panes(row_pos, 0)
        for line in tax_report_data:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._get_render_space(line),
                default_format=FORMATS["format_tcell_left"],
            )
        return row_pos

    def _write_ws_footer(self, row_pos, ws, ws_params, res_data):
        col_end = ws_params["wanted_list"].index("7_tax_base_amount")
        ws.merge_range(row_pos, 0, row_pos, col_end - 1, "")
        ws.write_row(
            row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
        )
        ws.write_row(
            row_pos,
            col_end,
            [
                res_data["total_base"],
                res_data["total_tax"],
                "",
            ],
            FORMATS["format_theader_blue_amount_right"],
        )
        return row_pos

    def _vat_report(self, wb, ws, ws_params, data, obj):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_thai_tax"
        ]._get_report_values(obj.ids, data)
        row_pos = 0
        header_data_list = self._get_header_data_list(res_data)
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        row_pos = self._write_ws_header(row_pos, ws, header_data_list)
        row_pos = self._write_ws_lines(
            row_pos, ws, ws_params, res_data["tax_report_data"]
        )
        row_pos = self._write_ws_footer(row_pos, ws, ws_params, res_data)

    def _get_header_data_list(self, res_data):
        return [
            ("Date From", res_data["date_from"].strftime("%d/%m/%Y") or "-"),
            ("Date To", res_data["date_to"].strftime("%d/%m/%Y") or "-"),
            ("Company", res_data["company_name"] or "-"),
            ("Company Tax ID", res_data["company_vat"] or "-"),
            ("Company Tax Branch", res_data["company_branch"] or "-"),
        ]
