# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        self._assign_tax_invoice()
        res = super()._post(soft)
        self._reconcile_withholding_tax_entry()
        return res

    def _reconcile_withholding_tax_entry(self):
        """Re-Reconciliation, for case wht_move that clear advance only"""
        PartialReconcile = self.env["account.partial.reconcile"]
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
            # Find all related clearings, advance and return moves to unreconcile first
            if move.line_ids.filtered(lambda l: l.account_id == av_account):
                all_clearings = advance.clearing_sheet_ids
                r_lines = all_clearings.mapped("account_move_id.line_ids").filtered(
                    lambda l: l.account_id == av_account
                )
                md_lines = r_lines.mapped("matched_debit_ids.debit_move_id")
                # Make sure that debit there're all line in advance
                av_move_lines = advance.account_move_id.line_ids.filtered(
                    lambda l: l.account_id == av_account
                )
                md_lines += av_move_lines
                # all reconcile move include return advance
                move_reconcile = PartialReconcile.search(
                    [("debit_move_id", "in", md_lines.ids)]
                )
                mc_lines_all = move_reconcile.mapped("credit_move_id")
                # Removes reconcile with all wht lines and only expenses
                wht_lines = all_clearings.mapped("wht_move_id.line_ids").filtered(
                    lambda l: l.account_id == av_account
                )
                wht_lines.remove_move_reconcile()
                # Removes reconcile with only expenses
                (md_lines + mc_lines_all).filtered(
                    lambda l: l.expense_id
                ).remove_move_reconcile()
                # Re-reconcile again this time with the wht_tax JV, account by account
                wht_lines_reconcile = wht_lines.filtered(
                    lambda l: l.parent_state == "posted"
                )
                md_lines_without_wht = md_lines.filtered(
                    lambda l: l.id not in wht_lines_reconcile.ids
                )
                (wht_lines_reconcile + md_lines_without_wht + mc_lines_all).reconcile()

            # Then, in case there are left over amount to other AP, do reconcile.
            ap_accounts = move.line_ids.mapped("account_id").filtered(
                lambda l: l.reconcile and l != av_account
            )
            for account in ap_accounts:
                ml_lines = (
                    clearing.account_move_id.line_ids + clearing.wht_move_id.line_ids
                )
                ml_lines.filtered(lambda l: l.account_id == account).reconcile()

    def _assign_tax_invoice(self):
        """Use Bill Reference and Date from Expense Line as Tax Invoice"""
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
        """Prepare dict for account.withholding.move on Expense"""
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

    def button_draft(self):
        """Unlink withholding tax on clearing"""
        res = super().button_draft()
        self._reconcile_withholding_tax_entry()
        return res

    def button_cancel(self):
        """Check Withholding tax JV before cancel journal entry on clearing"""
        res = super().button_cancel()
        sheets = self.line_ids.mapped("expense_id.sheet_id").filtered(
            lambda l: l.wht_move_id and l.wht_move_id.state != "cancel"
        )
        if sheets:
            raise UserError(
                _(
                    "Unable to cancel this journal entry. "
                    "You must first cancel the related withholding tax (Journal Voucher)."
                )
            )
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_tax_base_amount(self, sign, vals_list):
        """Case expense multi line, tax base amount should compute each line"""
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
