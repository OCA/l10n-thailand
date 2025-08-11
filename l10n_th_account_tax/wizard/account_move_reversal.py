# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    tax_invoice_number = fields.Char(copy=False)
    tax_invoice_date = fields.Date(copy=False)

    def reverse_moves(self):
        self.ensure_one()
        # Send context to reverse moves for case Full Refund
        # because it will auto post moves
        if self.move_type in ("in_invoice", "entry"):
            self = self.with_context(
                tax_invoice_number=self.tax_invoice_number,
                tax_invoice_date=self.tax_invoice_date,
            )
        action = super().reverse_moves()

        # Reverse moves with Partial Refund or Full refund and new draft invoice
        # Update tax invoice number and tax invoice date
        if (
            self.move_type in ("in_invoice", "entry")
            and self.tax_invoice_number
            and self.tax_invoice_date
        ):
            move_resversal = self.env[action["res_model"]].browse(action["res_id"])
            if not move_resversal.tax_invoice_ids.mapped("tax_invoice_number"):
                move_resversal.tax_invoice_ids.write(
                    {
                        "tax_invoice_number": self.tax_invoice_number,
                        "tax_invoice_date": self.tax_invoice_date,
                    }
                )
        return action
