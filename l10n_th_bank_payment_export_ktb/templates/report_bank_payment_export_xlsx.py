# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


class BankPaymentExportXslx(models.AbstractModel):
    _inherit = "report.bank.payment.export.xlsx"

    def _get_header_data_list(self, obj):
        header_data_list = super()._get_header_data_list(obj)
        if obj.bank == "KRTHTHBK":
            name_ktb_service_type = (
                obj.ktb_bank_type == "direct"
                and dict(obj._fields["ktb_service_type_direct"].selection).get(
                    obj.ktb_service_type_direct
                )
                or dict(obj._fields["ktb_service_type_standard"].selection).get(
                    obj.ktb_service_type_standard
                )
            )
            header_data_list.extend(
                [
                    (
                        "Type",
                        dict(obj._fields["ktb_bank_type"].selection).get(
                            obj.ktb_bank_type
                        )
                        or "-",
                    ),
                    ("Service Type", name_ktb_service_type),
                    ("Effective Date", obj.effective_date.strftime("%d/%m/%Y")),
                ]
            )
        return header_data_list

    def _get_render_space_ktb(self, idx, pe_line):
        return {
            "email": pe_line.payment_partner_id.ktb_email or "",
            "sms": pe_line.payment_partner_id.ktb_sms or "",
        }

    def _get_render_space(self, idx, pe_line, obj):
        render_space = super()._get_render_space(idx, pe_line, obj)
        if obj.bank == "KRTHTHBK":
            render_space.update(self._get_render_space_ktb(idx, pe_line))
        return render_space

    def _get_export_payment_vals(self, obj):
        """Addition of email and sms for KTB"""
        vals = super()._get_export_payment_vals(obj)
        if obj.bank == "KRTHTHBK":
            vals["11_email"] = {
                "header": {"value": "Email"},
                "data": {"value": self._render("email")},
                "width": 20,
            }
            vals["12_sms"] = {
                "header": {"value": "SMS"},
                "data": {"value": self._render("sms")},
                "width": 20,
            }
        return vals

    def _set_range_footer(self, row_pos, ws, obj):
        if obj.bank == "KRTHTHBK":
            ws.merge_range(row_pos, 0, row_pos, 6, "")
            ws.merge_range(row_pos, 8, row_pos, 11, "")
            ws.write_row(
                row_pos, 0, ["Total Balance"], FORMATS["format_theader_blue_right"]
            )
            return
        return super()._set_range_footer(row_pos, ws, obj)
