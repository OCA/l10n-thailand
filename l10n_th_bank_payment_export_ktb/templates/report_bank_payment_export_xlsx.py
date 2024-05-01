# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


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
