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
        """ Re-Reconciliation, for case wht_move that clear advance only """
        for move in self:
            clearing = self.env["hr.expense.sheet"].search(
                [("wht_move_id", "=", move.id)]
            )
            if not clearing:
                continue
            advance = clearing.advance_sheet_id
            clearing.ensure_one()
            # Find Advance account (from advance sheet)
            av_account = advance.expense_line_ids.mapped("account_id")
            av_account.ensure_one()
            # Find all related clearings and advance moves to unreconcile first
            if move.line_ids.filtered(lambda l: l.account_id == av_account):
                all_clearings = clearing.advance_sheet_id.clearing_sheet_ids
                r_lines = all_clearings.mapped("account_move_id.line_ids").filtered(
                    lambda l: l.account_id == av_account
                )
                md_lines = r_lines.mapped("matched_debit_ids.debit_move_id")
                mc_lines = r_lines.mapped("matched_credit_ids.credit_move_id")
                # Removes reconcile
                (r_lines + md_lines + mc_lines).remove_move_reconcile()
                # Re-reconcile again this time with the wht_tax JV, account by account
                wht_lines = all_clearings.mapped("wht_move_id.line_ids").filtered(
                    lambda l: l.account_id == av_account
                )
                to_reconciles = (r_lines + wht_lines + md_lines + mc_lines).filtered(
                    lambda l: not l.reconciled
                )
                to_reconciles.filtered(lambda l: l.account_id == av_account).reconcile()
            # Re-compute residual advance
            move._update_remaining_advance(advance)
            # Then, in case there are left over amount to other AP, do reconcile.
            ap_accounts = move.line_ids.mapped("account_id").filtered(
                lambda l: l.reconcile and l != av_account
            )
            if not ap_accounts:
                continue
            for account in ap_accounts:
                ml_lines = (
                    clearing.account_move_id.line_ids + clearing.wht_move_id.line_ids
                )
                ml_lines.filtered(lambda l: l.account_id == account).reconcile()

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

    def _update_remaining_advance(self, advance):
        """ If there is a return advance, update the clearing residual. """
        self.ensure_one()
        return_advance_ids = advance.payment_ids.filtered(
            lambda l: l.payment_type == "inbound"
        )
        # Case clearing > Advance, it should equal amount total (move)
        if not advance.clearing_residual:
            advance.clearing_residual += self.amount_total
            return
        for return_av in return_advance_ids:
            if advance.clearing_residual > 0.0:
                advance.clearing_residual -= return_av.move_id.amount_total


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_tax_base_amount(self, sign, vals_list):
        """ Case expense multi line, tax base amount should compute each line """
        tax_base_amount = super()._get_tax_base_amount(sign, vals_list)
        taxes_list = list(filter(lambda x: x.get("tax_repartition_line_id"), vals_list))
        for vals in taxes_list:
            if vals["move_id"] == self.move_id.id:
                line_ids = self.move_id.tax_cash_basis_move_id.line_ids
                move_line_tax_amount = line_ids.filtered(
                    lambda l: l.tax_base_amount
                    and l.amount_currency == self.amount_currency
                )
                if move_line_tax_amount:
                    tax_base_amount = move_line_tax_amount[0].tax_base_amount
        return tax_base_amount
