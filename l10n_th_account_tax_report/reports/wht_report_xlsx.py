# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class ReportWHTXlsx(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_withholding_tax_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report Withholding Tax xlsx"

    def _get_wht_template(self):
        return {
            "01_index": {
                "header": {"value": "No."},
                "data": {
                    "value": self._render("index"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 3,
            },
            "02_partner_vat": {
                "header": {"value": "Tax Invoice"},
                "data": {
                    "value": self._render("partner_vat"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 16,
            },
            "03_partner_name": {
                "header": {"value": "Cus./Sup."},
                "data": {"value": self._render("partner_name")},
                "width": 18,
            },
            "04_partner_address": {
                "header": {"value": "Address"},
                "data": {"value": self._render("partner_address")},
                "width": 20,
            },
            "05_cert_date_str": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("cert_date_str"),
                },
                "width": 10,
            },
            "06_wht_cert_income_desc": {
                "header": {"value": "Income Description"},
                "data": {"value": self._render("wht_cert_income_desc")},
                "width": 18,
            },
            "07_wht_percent": {
                "header": {"value": "Tax"},
                "data": {
                    "value": self._render("wht_percent"),
                    "type": "number",
                    "format": FORMATS["format_tcell_percent_conditional_right"],
                },
                "width": 8,
            },
            "08_base_amount": {
                "header": {"value": "Base Amount"},
                "data": {
                    "value": self._render("base_amount"),
                    "type": "number",
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 13,
            },
            "09_tax_amount": {
                "header": {"value": "Tax Amount"},
                "data": {
                    "value": self._render("tax_amount"),
                    "type": "number",
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 13,
            },
            "10_cert_tax_payer_display": {
                "header": {"value": "Tax Payer"},
                "data": {
                    "value": self._render("cert_tax_payer_display"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 12,
            },
            "11_cert_name": {
                "header": {"value": "Doc Ref."},
                "data": {"value": self._render("cert_name")},
                "width": 19,
            },
        }

    def _get_ws_params(self, wb, data, obj):
        withholding_tax_template = self._get_wht_template()
        ws_params = {
            "ws_name": "Withholding Tax Report",
            "generate_ws_method": "_withholding_tax_report",
            "title": f"Withholding Tax Report - {obj.company_id.name}",
            "wanted_list": [x for x in sorted(withholding_tax_template.keys())],
            "col_specs": withholding_tax_template,
        }

        return [ws_params]

    def _get_render_space(self, line):
        return {
            "index": line["row_number"],
            "partner_vat": line["partner_vat"] or "",
            "partner_name": line["partner_name"],
            "partner_address": line["partner_address"],
            "cert_date_str": line["cert_date_str"],
            "wht_cert_income_desc": line["wht_cert_income_desc"] or "",
            "wht_percent": line["wht_percent"] / 100 or 0.00,
            "base_amount": line["base"],
            "tax_amount": line["amount"],
            "cert_tax_payer_display": line["cert_tax_payer_display"],
            "cert_name": line["cert_name"],
        }

    def _write_ws_header(self, row_pos, ws, data_list):
        for data in data_list:
            ws.merge_range(row_pos, 0, row_pos, 1, "")
            ws.write_row(row_pos, 0, [data[0]], FORMATS["format_theader_blue_left"])
            ws.merge_range(row_pos, 2, row_pos, 3, "")
            ws.write_row(row_pos, 2, [data[1]])
            row_pos += 1
        return row_pos + 1

    def _write_ws_lines(self, row_pos, ws, ws_params, wht_report_data):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )
        ws.freeze_panes(row_pos, 0)
        for line in wht_report_data:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._get_render_space(line),
                default_format=FORMATS["format_tcell_left"],
            )
        return row_pos

    def _write_ws_footer(self, row_pos, ws, res_data):
        ws.merge_range(row_pos, 0, row_pos, 6, "")
        ws.merge_range(row_pos, 9, row_pos, 10, "")
        ws.write_row(
            row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
        )
        ws.write_row(
            row_pos,
            7,
            [res_data["total_base"], res_data["total_wht"], ""],
            FORMATS["format_theader_blue_amount_right"],
        )
        return row_pos

    def _get_header_data_list(self, res_data, obj):
        return [
            (
                "Date range filter",
                res_data["date_from"].strftime("%d/%m/%Y")
                + " - "
                + res_data["date_to"].strftime("%d/%m/%Y"),
            ),
            (
                "Income Tax Form",
                dict(obj._fields["income_tax_form"].selection).get(
                    res_data["income_tax_form"]
                ),
            ),
            ("Tax ID", res_data["company_vat"] or "-"),
            ("Branch ID", res_data["company_branch"] or "-"),
        ]

    def _withholding_tax_report(self, workbook, ws, ws_params, data, obj):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax"
        ]._get_report_values(obj.ids, data)
        row_pos = 0
        header_data_list = self._get_header_data_list(res_data, obj)
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        row_pos = self._write_ws_header(row_pos, ws, header_data_list)
        row_pos = self._write_ws_lines(
            row_pos, ws, ws_params, res_data["wht_report_data"]
        )
        row_pos = self._write_ws_footer(row_pos, ws, res_data)
        return row_pos
