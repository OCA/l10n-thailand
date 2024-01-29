# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    is_ac_payee = fields.Boolean(
        string="A/C. Payee Only",
    )
    lang_amount_check = fields.Selection(
        selection=[("en_US", "English"), ("th_TH", "Thai")],
        string="Language Amount Word",
        required=True,
        default=lambda self: self.env.user.lang,
    )

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals["is_ac_payee"] = self.is_ac_payee
        payment_vals["lang_amount_check"] = self.lang_amount_check
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = super()._create_payment_vals_from_batch(batch_result)
        batch_values["is_ac_payee"] = self.is_ac_payee
        batch_values["lang_amount_check"] = self.lang_amount_check
        return batch_values
