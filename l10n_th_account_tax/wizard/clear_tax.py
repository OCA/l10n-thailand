# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ClearTax(models.TransientModel):
    _name = "clear.tax"
    _description = "Clear Tax Wizard"

    date = fields.Date(
        string="Accounting Date (Tax Cash Basis)",
        required=True,
        default=fields.Date.context_today,
    )
    payment_id = fields.Many2one(
        "account.payment",
        string="Payment",
        required=True,
    )

    def action_clear_tax(self):
        self.ensure_one()
        payment = self.payment_id
        for tax_invoice in payment.tax_invoice_ids:
            # Update tax cash basis move date
            if tax_invoice.move_id.tax_cash_basis_origin_move_id:
                tax_invoice.move_id.write({"date": self.date})
        # Clear tax cash basis
        return payment.clear_tax_cash_basis()
