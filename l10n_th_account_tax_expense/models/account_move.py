# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        res = super()._post(soft)
        self._reconcile_withholding_tax_entry()
        return res

    def _reconcile_withholding_tax_entry(self):
        """Re-Reconciliation, for case wht_move that clear advance only"""
        sheet_model = self.env["hr.expense.sheet"]

        for move in self:
            clearing = sheet_model.search([("wht_move_id", "=", move.id)])
            if not clearing:
                continue

            clearing.ensure_one()
            advance = clearing.advance_sheet_id

            # Find Advance account (from advance sheet)
            av_account = advance.expense_line_ids.mapped("account_id")
            av_account.ensure_one()
            ml_advance = advance.account_move_ids.line_ids.filtered(
                lambda line, av_account=av_account: line.account_id == av_account
            )
            # Get all move line reconcile with advance
            ml_reconciled = ml_advance._all_reconciled_lines()
            # Get wht line with posted state only
            wht_line = move.line_ids.filtered(
                lambda line, av_account=av_account: line.account_id == av_account
                and line.parent_state == "posted"
            )
            # Remove reconcile
            all_ml_reconciled = ml_reconciled + wht_line
            all_ml_reconciled.remove_move_reconcile()
            # Clear cache
            all_ml_reconciled.invalidate_recordset()
            # Re-Reconcile with wht
            all_ml_reconciled.reconcile()

    def _compute_has_wht(self):
        """Has WHT when
        Is expense's JE when (
            move_type == 'entry'
            and lines with expense_id
            and not lines with payment_id
        )
        """
        res = super()._compute_has_wht()
        for rec in self.filtered("has_wht"):
            exp_move = (
                rec.move_type == "entry"
                and rec.line_ids.filtered("expense_id")
                and not rec.line_ids.filtered("payment_id")
            )
            rec.has_wht = False if exp_move else True
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
            lambda sheet: sheet.wht_move_id and sheet.wht_move_id.state != "cancel"
        )
        if sheets:
            raise UserError(
                _(
                    "Unable to cancel this journal entry. You must first cancel "
                    "the related withholding tax (Journal Voucher)."
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
                line_ids = self.move_id.tax_cash_basis_origin_move_id.line_ids
                move_line_tax_amount = line_ids.filtered(
                    lambda line: line.tax_base_amount
                    and line.amount_currency == self.amount_currency
                )
                if move_line_tax_amount:
                    tax_base_amount = move_line_tax_amount[0].tax_base_amount
        return tax_base_amount

    def _get_partner_wht_lines(self, wht_tax_lines, partner_id):
        if wht_tax_lines.filtered("expense_id"):
            partner_wht_lines = wht_tax_lines.filtered(
                lambda line: line.expense_id.bill_partner_id.id == partner_id
                or (
                    not line.expense_id.bill_partner_id
                    and line.partner_id.id == partner_id
                )
            )
            return partner_wht_lines
        return super()._get_partner_wht_lines(wht_tax_lines, partner_id)

    def _get_partner_wht(self, wht_tax_lines):
        if wht_tax_lines.filtered("expense_id"):
            partner_expense = wht_tax_lines.mapped("expense_id.bill_partner_id").ids
            return partner_expense
        return super()._get_partner_wht(wht_tax_lines)
