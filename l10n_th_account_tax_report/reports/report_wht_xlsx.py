# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class WithholdingTaxReportXslx(models.AbstractModel):
    _name = "report.withholding.tax.report.xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report Withholding Tax xlsx"

    def _define_formats(self, workbook):
        res = super()._define_formats(workbook)
        date_format = "DD/MM/YYYY"
        FORMATS["format_date_dmy_right"] = workbook.add_format(
            {"align": "right", "num_format": date_format}
        )
        return res

    def _get_ws_params(self, wb, data, obj):
        withholding_tax_template = {
            "01_sequence": {
                "header": {"value": "No."},
                "data": {
                    "value": self._render("sequence"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 3,
            },
            "02_vat": {
                "header": {"value": "Tax Invoice"},
                "data": {
                    "value": self._render("vat"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 16,
            },
            "03_display_name": {
                "header": {"value": "Cus./Sup."},
                "data": {"value": self._render("display_name")},
                "width": 18,
            },
            "04_street": {
                "header": {"value": "Address"},
                "data": {"value": self._render("street")},
                "width": 20,
            },
            "05_date": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("date"),
                    "type": "datetime",
                    "format": FORMATS["format_date_dmy_right"],
                },
                "width": 10,
            },
            "06_income_desc": {
                "header": {"value": "Income Description"},
                "data": {"value": self._render("income_desc")},
                "width": 18,
            },
            "07_tax": {
                "header": {"value": "Tax"},
                "data": {
                    "value": self._render("tax"),
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
            "10_tax_payer": {
                "header": {"value": "Tax Payer"},
                "data": {
                    "value": self._render("tax_payer"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 12,
            },
            "11_payment_id": {
                "header": {"value": "Doc Ref."},
                "data": {"value": self._render("payment_id")},
                "width": 19,
            },
        }

        ws_params = {
            "ws_name": "Withholding Tax Report",
            "generate_ws_method": "_withholding_tax_report",
            "title": "Withholding Tax Report - %s" % (obj.company_id.name),
            "wanted_list": [x for x in sorted(withholding_tax_template.keys())],
            "col_specs": withholding_tax_template,
        }

        return [ws_params]

    def _write_ws_header(self, row_pos, ws, data_list):
        for data in data_list:
            ws.merge_range(row_pos, 0, row_pos, 1, "")
            ws.write_row(row_pos, 0, [data[0]], FORMATS["format_theader_blue_left"])
            ws.merge_range(row_pos, 2, row_pos, 3, "")
            ws.write_row(row_pos, 2, [data[1]])
            row_pos += 1
        return row_pos + 1

    def _write_ws_lines(self, row_pos, ws, ws_params, obj):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )
        ws.freeze_panes(row_pos, 0)
        index = 1
        for line in obj.results:
            cancel = line.cert_id.state == "cancel"
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "sequence": index,
                    "vat": line.cert_id.partner_id.vat or "",
                    "display_name": not cancel
                    and line.cert_id.partner_id.display_name
                    or "Cancelled",
                    "street": not cancel and line.cert_id.partner_id.street or "",
                    "date": line.cert_id.date,
                    "income_desc": line.wht_cert_income_desc or "",
                    "tax": line.wht_percent / 100 or 0.00,
                    "base_amount": not cancel and line.base or 0.00,
                    "tax_amount": not cancel and line.amount or 0.00,
                    "tax_payer": line.cert_id.tax_payer,
                    "payment_id": line.cert_id.name,
                },
                default_format=FORMATS["format_tcell_left"],
            )
            index += 1
        return row_pos

    def _write_ws_footer(self, row_pos, ws, obj):
        results = obj.results.filtered(lambda l: l.cert_id.state == "done")
        ws.merge_range(row_pos, 0, row_pos, 6, "")
        ws.merge_range(row_pos, 9, row_pos, 10, "")
        ws.write_row(
            row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
        )
        ws.write_row(
            row_pos,
            7,
            [sum(results.mapped("base")), sum(results.mapped("amount")), ""],
            FORMATS["format_theader_blue_amount_right"],
        )
        return row_pos

    def _withholding_tax_report(self, workbook, ws, ws_params, data, obj):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        row_pos = 0
        header_data_list = [
            (
                "Date range filter",
                obj.date_from.strftime("%d/%m/%Y")
                + " - "
                + obj.date_to.strftime("%d/%m/%Y"),
            ),
            (
                "Income Tax Form",
                dict(obj._fields["income_tax_form"].selection).get(obj.income_tax_form),
            ),
            ("Currency", obj.company_id.currency_id.name),
            ("Tax ID", obj.company_id.partner_id.vat or "-"),
            ("Branch ID", obj.company_id.partner_id.branch or "-"),
        ]
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        row_pos = self._write_ws_header(row_pos, ws, header_data_list)
        row_pos = self._write_ws_lines(row_pos, ws, ws_params, obj)
        row_pos = self._write_ws_footer(row_pos, ws, obj)
        return row_pos
