# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    tax_invoice_number = fields.Char(copy=False)
    tax_invoice_date = fields.Date(copy=False)

    def reverse_moves(self, is_modify=False):
        """The vendor issues the credit note with its own tax invoice"""
        self.ensure_one()
        wizard = self
        if self.move_type in ("in_invoice", "in_refund"):
            wizard = self.with_context(
                tax_invoice_number=self.tax_invoice_number,
                tax_invoice_date=self.tax_invoice_date,
            )
        return super(AccountMoveReversal, wizard).reverse_moves(is_modify)
