# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    wt_tax_id = fields.Many2one(
        string="Withholding Tax",
        comodel_name="account.withholding.tax",
        help="Optional hidden field to keep wt_tax. Useful for case 1 tax only",
    )

    def _update_payment_register(self, amount_wt, inv_lines):
        self.ensure_one()
        self.amount -= amount_wt
        self.payment_difference_handling = "reconcile"
        wt_tax = inv_lines.mapped("wt_tax_id")
        if wt_tax and len(wt_tax) == 1:
            self.wt_tax_id = wt_tax
        return True

    @api.onchange("currency_id")
    def _onchange_currency(self):
        res = super()._onchange_currency()
        # Get the sum withholding tax amount from invoice line
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            inv_lines = invoices.mapped("invoice_line_ids").filtered("wt_tax_id")
            amount_wt = sum(
                inv_lines.mapped(lambda l: l.wt_tax_id.amount / 100 * l.price_subtotal)
            )
            if amount_wt:
                self._update_payment_register(amount_wt, inv_lines)
        return res

    @api.onchange("wt_tax_id")
    def _onchange_wt_tax_id(self):
        if self.wt_tax_id:
            self.writeoff_account_id = self.wt_tax_id.account_id
            self.writeoff_label = self.wt_tax_id.display_name
