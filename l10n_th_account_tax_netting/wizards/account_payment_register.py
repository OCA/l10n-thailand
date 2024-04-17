# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _onchange_wht(self):
        """
        Reversing signs for cases with withholding tax on different sides
        of the payment (netting). For case,
            1. AP > AR but withholding tax is applied on AR
            2. AP < AR but withholding tax is applied by AP
        """
        res = super()._onchange_wht()
        if self.env.context.get("netting") and (
            (self.payment_type == "inbound" and self.wht_amount_base > 0.0)
            or (self.payment_type == "outbound" and self.wht_amount_base < 0.0)
        ):
            amount_wht = -(self.wht_tax_id.amount / 100) * self.wht_amount_base
            amount_currency = self.company_id.currency_id._convert(
                self.source_amount,
                self.currency_id,
                self.company_id,
                self.payment_date,
            )
            self.amount = amount_currency - amount_wht
        return res
