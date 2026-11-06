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
        comodel_name="account.payment",
        required=True,
    )

    def action_clear_tax(self):
        self.ensure_one()
        return self.payment_id.clear_tax_cash_basis(date=self.date)
