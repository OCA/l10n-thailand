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
            # Find clearing and advance moves to unreconcile first
            r_lines = clearing.account_move_id.line_ids.filtered(
                lambda l: l.account_id.id in accounts.ids
            )
            md_lines = r_lines.mapped("matched_debit_ids.debit_move_id")
            mc_lines = r_lines.mapped("matched_credit_ids.credit_move_id")
            # Removes reconcile
            (r_lines + md_lines + mc_lines).remove_move_reconcile()
            # Re-reconcile again this time with the wht_tax JV
            wht_lines = move.line_ids.filtered(
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
