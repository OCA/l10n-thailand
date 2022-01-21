# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _update_payment_register(self, amount_base, amount_wht, wht_move_lines):
        res = super()._update_payment_register(amount_base, amount_wht, wht_move_lines)
        if self.payment_difference_handling == "reconcile":
            self._onchange_default_deduction()
        return res
