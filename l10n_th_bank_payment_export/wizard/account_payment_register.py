# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    is_export = fields.Boolean(
        string="Bank Payment Exported",
        help="if checked, it means the money has already been sent to the bank.",
    )
    bank_payment_template_id = fields.Many2one(
        comodel_name="bank.payment.template",
        compute="_compute_bank_payment_template",
        readonly=False,
        check_company=True,
        store=True,
    )

    @api.depends("partner_id")
    def _compute_bank_payment_template(self):
        for wizard in self:
            wizard.bank_payment_template_id = (
                wizard.partner_id.property_bank_payment_template_id.id
            )

    def _update_export_status(self, payment_vals):
        payment_vals["export_status"] = self.is_export and "exported" or "draft"
        payment_vals["bank_payment_template_id"] = self.bank_payment_template_id.id
        return payment_vals

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals = self._update_export_status(payment_vals)
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        payment_vals = self._update_export_status(payment_vals)
        return payment_vals
