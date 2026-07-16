# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, api, fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    tax_invoice_number = fields.Char(copy=False)
    tax_invoice_date = fields.Date(copy=False)
    show_reverse_taxes = fields.Boolean(compute="_compute_show_reverse_taxes")
    use_reverse_taxes = fields.Boolean(
        string="Reverse Tax",
        compute="_compute_use_reverse_taxes",
        store=True,
        readonly=False,
        help="For a fully paid invoice, book the credit note VAT to the due tax "
        "account (e.g. Output VAT) instead of the undue/suspense account.",
    )

    def _is_reverse_taxes_eligible(self):
        self.ensure_one()
        moves = self.move_ids
        return (
            bool(moves)
            and all(move.payment_state in ("paid", "in_payment") for move in moves)
            and bool(moves.invoice_line_ids.tax_ids.filtered("reverse_tax_id"))
        )

    @api.depends("move_ids")
    def _compute_show_reverse_taxes(self):
        for wiz in self:
            wiz.show_reverse_taxes = wiz._is_reverse_taxes_eligible()

    @api.depends("move_ids")
    def _compute_use_reverse_taxes(self):
        for wiz in self:
            wiz.use_reverse_taxes = wiz._is_reverse_taxes_eligible()

    def reverse_moves(self, is_modify=False):
        self.ensure_one()
        if self.move_type == "in_invoice":
            self = self.with_context(
                tax_invoice_number=self.tax_invoice_number,
                tax_invoice_date=self.tax_invoice_date,
            )
        action = super().reverse_moves(is_modify)
        if self.use_reverse_taxes and self.show_reverse_taxes:
            self._apply_reverse_taxes(self.new_move_ids)
        return action

    def _swapped_taxes(self, taxes):
        """Replace each undue tax by its reverse (due) tax, keep the rest."""
        result = self.env["account.tax"]
        for tax in taxes:
            result |= tax.reverse_tax_id or tax
        return result

    def _apply_reverse_taxes(self, moves):
        for move in moves.filtered(
            lambda m: m.state == "draft"
            and m.move_type in ("out_refund", "in_refund")
            and m.reversed_entry_id
        ):
            # Collect all line changes and apply them in a single move.write so
            # account.move._sync_dynamic_lines recomputes the tax lines.
            commands = []
            for line in move.invoice_line_ids:
                if not line.tax_ids.filtered("reverse_tax_id"):
                    continue
                commands.append(
                    Command.update(
                        line.id,
                        {
                            "tax_ids": [
                                Command.set(self._swapped_taxes(line.tax_ids).ids)
                            ]
                        },
                    )
                )
            if commands:
                move.write({"invoice_line_ids": commands})
