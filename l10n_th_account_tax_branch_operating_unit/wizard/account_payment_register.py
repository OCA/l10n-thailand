# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_reconciled_all_moves(self, payment):
        reconciled_moves = super()._get_reconciled_all_moves(payment)
        if not payment.branch_id:
            move_branch = list({move.branch_id.id for move in reconciled_moves})
            if any(move_branch):
                payment_branch = move_branch[0] if len(move_branch) == 1 else False
                if not payment_branch:
                    reconciled_moves = reconciled_moves.filtered(
                        lambda l: not l.branch_id
                    )
                else:
                    reconciled_moves = reconciled_moves.filtered(
                        lambda l: l.branch_id.id == payment_branch
                    )
        return reconciled_moves

    def _get_branch_origin(self, payment_vals):
        """Branch Payment Conditions:
        1. Registering a payment involving multiple branches will leave
            the branch field empty.
        2. When registering a payment with a single branch,
            the branch will get value from the origin.
        3. In cases where no branch is specified during payment registration,
            the branch will get value from the payment journal.
        """
        moves = self.line_ids.mapped("move_id")
        move_branch = list({move.branch_id.id for move in moves})
        if any(move_branch):
            payment_vals["branch_id"] = (
                move_branch[0] if len(move_branch) == 1 else False
            )
        return payment_vals

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals = self._get_branch_origin(payment_vals)
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        payment_vals = self._get_branch_origin(payment_vals)
        return payment_vals
