# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models


class WithholdingTaxReportXslx(models.AbstractModel):
    _name = "report.withholding.tax.report.xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Report Withholding Tax xlsx"

    def _get_ws_params(self, wb, data, objects):
        withholding_tax_template = {
            "sequence": {
                "header": {"value": "No."},
                "data": {
                    "value": self._render("sequence"),
                    "format": self.format_tcell_center,
                },
                "width": 3,
            },
            "vat": {
                "header": {"value": "Tax Invoice"},
                "data": {
                    "value": self._render("vat"),
                    "format": self.format_tcell_center,
                },
                "width": 16,
            },
            "display_name": {
                "header": {"value": "Cus./Sup."},
                "data": {"value": self._render("display_name")},
                "width": 18,
            },
            "street": {
                "header": {"value": "Address"},
                "data": {"value": self._render("street")},
                "width": 20,
            },
            "date": {
                "header": {"value": "Date"},
                "data": {
                    "value": self._render("date"),
                    "type": "datetime",
                    "format": self.format_tcell_date_right,
                },
                "width": 10,
            },
            "income_desc": {
                "header": {"value": "Income Description"},
                "data": {"value": self._render("income_desc")},
                "width": 18,
            },
            "tax": {
                "header": {"value": "Tax"},
                "data": {
                    "value": self._render("tax"),
                    "type": "number",
                    "format": self.format_tcell_percent_conditional_right,
                },
                "width": 8,
            },
            "base_amount": {
                "header": {"value": "Base Amount"},
                "data": {
                    "value": self._render("base_amount"),
                    "type": "number",
                    "format": self.format_tcell_amount_right,
                },
                "width": 13,
            },
            "tax_amount": {
                "header": {"value": "Tax Amount"},
                "data": {
                    "value": self._render("tax_amount"),
                    "type": "number",
                    "format": self.format_tcell_amount_right,
                },
                "width": 13,
            },
            "tax_payer": {
                "header": {"value": "Tax Payer"},
                "data": {
                    "value": self._render("tax_payer"),
                    "format": self.format_tcell_center,
                },
                "width": 12,
            },
            "payment_id": {
                "header": {"value": "Doc Ref."},
                "data": {"value": self._render("payment_id")},
                "width": 19,
            },
        }

        ws_params = {
            "ws_name": "Withholding Tax Report",
            "generate_ws_method": "_withholding_tax_report",
            "title": "Withholding Tax Report - %s" % (objects.company_id.name),
            "wanted_list": [x for x in withholding_tax_template],
            "col_specs": withholding_tax_template,
        }

        return [ws_params]

    def _withholding_tax_report(self, workbook, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        ws.merge_range(row_pos, 0, row_pos, 1, "")
        ws.write_row(
            row_pos, 0, [_("Date range filter")], self.format_theader_yellow_center
        )
        ws.merge_range(row_pos, 2, row_pos, 3, "")
        ws.write_row(
            row_pos,
            2,
            [str(objects.date_to) + " - " + str(objects.date_to)],
            self.format_center,
        )
        row_pos += 1
        ws.merge_range(row_pos, 0, row_pos, 1, "")
        ws.write_row(
            row_pos, 0, [_("Income Tax Form")], self.format_theader_yellow_center
        )
        ws.merge_range(row_pos, 2, row_pos, 3, "")
        ws.write_row(row_pos, 2, [(objects.income_tax_form)], self.format_center)
        row_pos += 1
        ws.merge_range(row_pos, 0, row_pos, 1, "")
        ws.write_row(row_pos, 0, [_("Tax ID")], self.format_theader_yellow_center)
        ws.merge_range(row_pos, 2, row_pos, 3, "")
        ws.write_row(
            row_pos, 2, [(objects.company_id.partner_id.vat) or "-"], self.format_center
        )
        row_pos += 1
        ws.merge_range(row_pos, 0, row_pos, 1, "")
        ws.write_row(row_pos, 0, [_("Branch ID")], self.format_theader_yellow_center)
        ws.merge_range(row_pos, 2, row_pos, 3, "")
        ws.write_row(
            row_pos,
            2,
            [(objects.company_id.partner_id.branch) or "-"],
            self.format_center,
        )
        row_pos += 2
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_blue_center,
        )
        ws.freeze_panes(row_pos, 0)
        for obj in objects:
            for line in obj.results:
                row_pos = self._write_line(
                    ws,
                    row_pos,
                    ws_params,
                    col_specs_section="data",
                    render_space={
                        "sequence": row_pos - 7,
                        "vat": line.cert_id.supplier_partner_id.vat or "",
                        "display_name": line.cert_id.supplier_partner_id.display_name
                        or "",
                        "street": line.cert_id.supplier_partner_id.street,
                        "date": line.cert_id.date,
                        "income_desc": line.wt_cert_income_desc or "",
                        "tax": line.wt_percent / 100 or 0.00,
                        "base_amount": line.base or 0.00,
                        "tax_amount": line.amount or 0.00,
                        "tax_payer": line.cert_id.tax_payer,
                        "payment_id": line.cert_id.payment_id.name,
                    },
                    default_format=self.format_tcell_left,
                )
        ws.merge_range(row_pos, 0, row_pos, 6, "")
        ws.merge_range(row_pos, 9, row_pos, 10, "")
        ws.write_row(row_pos, 0, ["Total Balance"], self.format_theader_blue_center)
        ws.write_row(
            row_pos,
            7,
            [
                sum(objects.results.mapped("base")),
                sum(objects.results.mapped("amount")),
                "",
            ],
            self.format_theader_blue_amount_right,
        )
