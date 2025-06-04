# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class BankPaymentExportXslx(models.AbstractModel):
    _inherit = "report.bank.payment.export.xlsx"

    def _get_header_data_list(self, obj):
        header_data_list = super()._get_header_data_list(obj)
        if obj.bank == "BKKBTHBK":
            header_data_list.extend(
                [
                    (
                        "Type",
                        dict(obj._fields["bbl_bank_type"].selection).get(
                            obj.bbl_bank_type
                        )
                        or "-",
                    ),
                    ("Company Bank Account", obj.bbl_company_bank_account.acc_number),
                    (
                        "Product Code",
                        dict(obj._fields["bbl_product_code"].selection).get(
                            obj.bbl_product_code
                        ),
                    ),
                    (
                        "BOT service type",
                        dict(obj._fields["bbl_bot_type"].selection).get(
                            obj.bbl_bot_type
                        ),
                    ),
                    (
                        "Payee Charge",
                        dict(obj._fields["bbl_payee_charge"].selection).get(
                            obj.bbl_payee_charge
                        ),
                    ),
                    ("Credit Advice", obj.bbl_credit_advice and "Yes" or "No"),
                ]
            )
        return header_data_list
