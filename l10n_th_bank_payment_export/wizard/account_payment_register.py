# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    is_export = fields.Boolean(
        string="Bank Payment Exported",
        help="if checked, it means the money has already been sent to the bank.",
    )

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals["export_status"] = self.is_export and "exported" or "draft"
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        payment_vals["export_status"] = self.is_export and "exported" or "draft"
        return payment_vals
