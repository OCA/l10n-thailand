# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    wht_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Withholding Tax JV",
        ondelete="restrict",
        copy=False,
        readonly=True,
        help="For case clear advance, a JV can be created to record withholding tax",
    )
    has_wht = fields.Boolean(
        compute="_compute_has_wht",
    )

    def _compute_has_wht(self):
        for rec in self:
            rec.has_wht = len(rec.expense_line_ids.mapped("wht_tax_id")) > 0

    def action_create_withholding_tax_entry(self):
        """From expense sheet with WHT lines, this action
        helps create new JV with default withholding entries"""
        self.ensure_one()
        action = self.env.ref("account.action_move_journal_line")
        result = action.sudo().read()[0]
        view = self.env.ref("account.view_move_form", False)
        result["views"] = [(view and view.id or False, "form")]
        # Prepare Dr. Advance, Cr. WHT lines
        line_vals_list = []
        # Cr. WHT Lines
        wht_move_lines = self.account_move_id.mapped("line_ids").filtered("wht_tax_id")
        currency = self.env.company.currency_id
        deduction_list, amount_deduct = wht_move_lines._prepare_deduction_list(
            currency=currency
        )
        for deduction in deduction_list:
            line_vals_list.append(
                {
                    "name": deduction["name"],
                    "amount_currency": -deduction["amount"],
                    "currency_id": currency.id,
                    "debit": 0.0,
                    "credit": deduction["amount"],
                    "partner_id": deduction["partner_id"],
                    "account_id": deduction["account_id"],
                }
            )
        emp_advance = self.env.ref("hr_expense_advance_clearing.product_emp_advance")
        adv_account = emp_advance.property_account_expense_id
        # Dr. Advance
        line_vals_list.append(
            {
                "name": adv_account.name,
                "amount_currency": amount_deduct,
                "currency_id": currency.id,
                "debit": amount_deduct,  # Sum of all credit
                "credit": 0.0,
                "partner_id": self.employee_id.sudo().address_home_id.commercial_partner_id.id,
                "account_id": adv_account.id,
            }
        )
        # Create JV
        move_vals = {
            "move_type": "entry",
            "line_ids": [(0, 0, line_vals) for line_vals in line_vals_list],
        }
        move = self.env["account.move"].create(move_vals)
        self.wht_move_id = move
        result["res_id"] = move.id
        return result
