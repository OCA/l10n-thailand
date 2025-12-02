# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _get_move_type_cash_basis(self):
        return ["in_invoice", "entry"]

    def _update_state_cash_basis(self, moves):
        """Back state tax cash basis in bills and entry to draft
        not include net refund and payment. waiting clear tax later."""
        move_type = self._get_move_type_cash_basis()
        for move in moves:
            if move.tax_cash_basis_origin_move_id.move_type in move_type:
                move.mapped("line_ids").remove_move_reconcile()
                move.write({"state": "draft", "is_move_sent": False})

    def _create_tax_cash_basis_moves(self):
        """This method is called from the move lines that
        create cash basis entry. We want to use the same payment_id when
        create account.move.tax.invoice"""
        move_lines = self.debit_move_id | self.credit_move_id
        payment = move_lines.mapped("payment_id")
        if len(payment) == 1:
            self = self.with_context(payment_id=payment.id)

        if all(
            move.debit_move_id.move_type == "in_refund"
            and move.credit_move_id.move_type == "in_invoice"
            for move in self
        ):
            self = self.with_context(net_invoice_refund=1)

        moves = super()._create_tax_cash_basis_moves()
        # EXPERIMENT: remove income / expense account move lines
        ml_groups = self.env["account.move.line"].read_group(
            domain=[("move_id", "in", moves.ids)],
            fields=[
                "move_id",
                "account_id",
                "debit",
                "credit",
            ],
            groupby=[
                "move_id",
                "account_id",
            ],
            lazy=False,
        )
        del_ml_groups = list(
            filter(lambda line: line["debit"] == line["credit"], ml_groups)
        )
        account_ids = [g.get("account_id")[0] for g in del_ml_groups]
        # Not include taxes (0%) and not reconciled
        del_move_lines = moves.mapped("line_ids").filtered(
            lambda line: line.account_id.id in account_ids
            and not line.tax_line_id
            and not line.reconciled
        )
        if del_move_lines:
            self.env.cr.execute(
                "DELETE FROM account_move_line WHERE id in %s",
                (tuple(del_move_lines.ids),),
            )

        # Case: Vendor Bills only.
        # Reset tax cash basis to draft. until clear tax or reset payment
        # - Bill --> Payment
        #     create cash basis (1) is draft
        # - Payment (Posted) --> Payment (Draft)
        #     create cash basis (2) and reconcile with (1) state change to posted
        # - Bill manual reconcile payment
        #     create cash basis (3) is draft
        net_invoice_refund = self.env.context.get("net_invoice_refund")
        net_invoice_payment = self.env.context.get("net_invoice_payment")
        if not net_invoice_refund or net_invoice_payment:
            self._update_state_cash_basis(moves)
        return moves
