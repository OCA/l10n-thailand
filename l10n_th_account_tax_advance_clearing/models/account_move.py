# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """After post, for wht_tax JV case only, recompute the reconciliation
        to ensure that the wht_tax JV is taken into account first"""
        res = super()._post(soft=soft)
        for move in self:
            clearing = self.env["hr.expense.sheet"].search(
                [("wht_move_id", "=", move.id)]
            )
            if not clearing:
                continue
            clearing.ensure_one()
            emp_advance = self.env.ref(
                "hr_expense_advance_clearing.product_emp_advance"
            )
            adv_account = emp_advance.property_account_expense_id
            # Find clearing and advance moves to reconcile
            cl_lines = clearing.account_move_id.line_ids.filtered(
                lambda l: l.account_id == adv_account
            )
            av_lines = cl_lines.mapped("matched_debit_ids.debit_move_id")
            # Removes reconcile
            res = (cl_lines + av_lines).remove_move_reconcile()
            # reconcile again this time with the wht_tax JV
            wht_lines = move.line_ids.filtered(lambda l: l.account_id == adv_account)
            res = (cl_lines + wht_lines + av_lines).reconcile()
        return res
