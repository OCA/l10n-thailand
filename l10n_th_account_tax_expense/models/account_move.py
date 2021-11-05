# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        self._assign_tax_invoice()
        res = super()._post(soft)
        self._reconcile_withholding_tax_entry()
        return res

    def _reconcile_withholding_tax_entry(self):
        """ Re-Reconciliation, ensure the wht_move is taken into account """
        for move in self:
            clearing = self.env["hr.expense.sheet"].search(
                [("wht_move_id", "=", move.id)]
            )
            if not clearing:
                continue
            clearing.ensure_one()
            move_lines = clearing.account_move_id.line_ids
            accounts = move_lines.mapped("account_id").filtered("reconcile")
            # Find all related clearings and advance moves to unreconcile first
            all_clearings = clearing.advance_sheet_id.clearing_sheet_ids
            r_lines = all_clearings.mapped("account_move_id.line_ids").filtered(
                lambda l: l.account_id.id in accounts.ids
            )
            md_lines = r_lines.mapped("matched_debit_ids.debit_move_id")
            mc_lines = r_lines.mapped("matched_credit_ids.credit_move_id")
            # Removes reconcile
            (r_lines + md_lines + mc_lines).remove_move_reconcile()
            # Re-reconcile again this time with the wht_tax JV
            wht_lines = all_clearings.mapped("wht_move_id.line_ids").filtered(
                lambda l: l.account_id.id in accounts.ids
            )
            (r_lines + wht_lines + md_lines + mc_lines).reconcile()

    def _assign_tax_invoice(self):
        """ Use Bill Reference and Date from Expense Line as Tax Invoice """
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda l: l.tax_line_id.type_tax_use == "purchase"
            ):
                if tax_invoice.move_line_id.expense_id:
                    tinv_number = tax_invoice.move_line_id.expense_id.reference
                    tinv_date = tax_invoice.move_line_id.expense_id.date
                    tax_invoice.write(
                        {
                            "tax_invoice_number": tinv_number,
                            "tax_invoice_date": tinv_date,
                        }
                    )
                    bill_partner = tax_invoice.move_line_id.expense_id.bill_partner_id
                    if bill_partner:
                        tax_invoice.write({"partner_id": bill_partner.id})

    def _compute_has_wht(self):
        """Has WHT when
        Is expense's JE when (
            move_type == 'entry'
            and lines with expense_id
            and not lines with payment_id
        )
        """
        super()._compute_has_wht()
        for rec in self.filtered("has_wht"):
            exp_move = (
                rec.move_type == "entry"
                and rec.line_ids.filtered("expense_id")
                and not rec.line_ids.filtered("payment_id")
            )
            if exp_move:
                rec.has_wht = False

    def _prepare_withholding_move(self, wht_move):
        """ Prepare dict for account.withholding.move on Expense"""
        res = super()._prepare_withholding_move(wht_move)
        # Is this an expense's journal entry?
        is_expense = wht_move.expense_id and not wht_move.payment_id
        if is_expense:
            res.update(
                {
                    "amount_income": abs(wht_move.balance),
                    "amount_wht": 0.0,
                }
            )
        return res
