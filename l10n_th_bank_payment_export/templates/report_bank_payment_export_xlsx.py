# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class BankPaymentExportXslx(models.AbstractModel):
    _name = "report.bank.payment.export.xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Payment Export xlsx"

    def _get_export_payment_vals(self, obj):
        return {
            "01_sequence": {
                "header": {"value": "No."},
                "data": {
                    "value": self._render("sequence"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 3,
            },
            "02_reference": {
                "header": {"value": "Reference"},
                "data": {
                    "value": self._render("reference"),
                },
                "width": 20,
            },
            "03_payment_date": {
                "header": {"value": "Payment Date"},
                "data": {
                    "value": self._render("payment_date"),
                },
                "width": 15,
            },
            "04_partner": {
                "header": {"value": "Vendor"},
                "data": {
                    "value": self._render("partner"),
                },
                "width": 30,
            },
            "05_recipient_bank": {
                "header": {"value": "Account Number"},
                "data": {
                    "value": self._render("acc_number"),
                },
                "width": 20,
            },
            "06_recipient_bank_name": {
                "header": {"value": "Bank Name"},
                "data": {
                    "value": self._render("bank_name"),
                },
                "width": 20,
            },
            "07_recipient_bank_holder_name": {
                "header": {"value": "Account Holder Name"},
                "data": {
                    "value": self._render("acc_holder_name"),
                },
                "width": 30,
            },
            "08_amount": {
                "header": {
                    "value": "Amount ({})".format(self.env.company.currency_id.name)
                },
                "data": {
                    "value": self._render("amount"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 15,
            },
            "09_recipient_bank_code": {
                "header": {"value": "Bank Code"},
                "data": {
                    "value": self._render("bank_code"),
                },
                "width": 10,
            },
            "10_recipient_bank_branch_code": {
                "header": {"value": "Bank Branch Code"},
                "data": {
                    "value": self._render("bank_branch_code"),
                },
                "width": 10,
            },
            "11_email": {
                "header": {"value": "Email"},
                "data": {
                    "value": self._render("email"),
                },
                "width": 20,
            },
            "12_phone": {
                "header": {"value": "Phone"},
                "data": {
                    "value": self._render("phone"),
                },
                "width": 15,
            },
        }

    def _get_ws_params(self, wb, data, obj):
        export_payment_template = self._get_export_payment_vals(obj)
        ws_params = {
            "ws_name": "Export Payment Excel Report",
            "generate_ws_method": "_export_payment_report",
            "title": "Export Payment {}".format(
                dict(obj._fields["bank"].selection).get(obj.bank) or ""
            ),
            "wanted_list": [x for x in sorted(export_payment_template.keys())],
            "col_specs": export_payment_template,
        }

        return [ws_params]

    def _get_render_space(self, idx, pe_line, obj):
        recipient_bank = pe_line.payment_partner_bank_id
        acc_number = recipient_bank.acc_number or False
        received_bank = recipient_bank.bank_id
        partner_id = pe_line.payment_partner_id
        payment_net_amount = pe_line._get_payment_net_amount()
        return {
            "sequence": idx + 1,
            "reference": pe_line.payment_id.name,
            "payment_date": pe_line.payment_date.strftime("%d/%m/%Y"),
            "partner": partner_id.display_name or "",
            "acc_number": acc_number and acc_number.zfill(11) or "",
            "bank_name": received_bank.name or "",
            "acc_holder_name": recipient_bank.acc_holder_name
            or recipient_bank.partner_id.display_name
            or "",
            "amount": payment_net_amount,
            "bank_code": received_bank.bank_code or "",
            "bank_branch_code": received_bank.bank_branch_code or "",
            "email": partner_id.email or "",
            "phone": partner_id.phone or "",
        }

    def _get_header_data_list(self, obj):
        return [
            ("Bank", dict(obj._fields["bank"].selection).get(obj.bank) or "-"),
        ]

    def _write_ws_header(self, row_pos, ws, data_list):
        for data in data_list:
            ws.merge_range(row_pos, 0, row_pos, 1, "")
            ws.write_row(row_pos, 0, [data[0]], FORMATS["format_theader_blue_center"])
            ws.merge_range(row_pos, 2, row_pos, 3, "")
            ws.write_row(row_pos, 2, [data[1]])
            row_pos += 1
        return row_pos + 1

    def _write_ws_lines(self, row_pos, ws, ws_params, obj, payment_export_line):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )
        ws.freeze_panes(row_pos, 0)
        for idx, pe_line in enumerate(payment_export_line):
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._get_render_space(idx, pe_line, obj),
                default_format=FORMATS["format_tcell_left"],
            )
        return row_pos

    def _write_ws_footer(self, row_pos, ws, obj, payment_export_line):
        ws.merge_range(row_pos, 0, row_pos, 6, "")
        ws.merge_range(row_pos, 8, row_pos, 11, "")
        ws.write_row(
            row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
        )
        # TODO: Not support Multi Currency yet.
        total_balance_payment = sum(
            pe_line.currency_id._convert(
                pe_line.payment_amount,
                pe_line.payment_id.company_id.currency_id,
                pe_line.payment_id.company_id,
                pe_line.payment_date,
                round=False,
            )
            for pe_line in payment_export_line
        )
        ws.write_row(
            row_pos,
            7,
            [total_balance_payment, ""],
            FORMATS["format_theader_blue_amount_right"],
        )
        return row_pos

    def _export_payment_report(self, workbook, ws, ws_params, data, obj):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        row_pos = 0
        header_data_list = self._get_header_data_list(obj)
        payment_export_line = obj.export_line_ids
        row_pos = self._write_ws_title(ws, row_pos, ws_params, merge_range=True)
        row_pos = self._write_ws_header(row_pos, ws, header_data_list)
        row_pos = self._write_ws_lines(row_pos, ws, ws_params, obj, payment_export_line)
        row_pos = self._write_ws_footer(row_pos, ws, obj, payment_export_line)
        return row_pos
