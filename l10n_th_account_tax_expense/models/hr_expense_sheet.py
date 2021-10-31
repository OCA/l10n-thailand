# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, fields, models
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    wht_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Withholding Tax JV",
        ondelete="set null",
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
        active_id = self.env.context.get("active_id")
        sheet = self.env["hr.expense.sheet"].browse(active_id)
        sheet.ensure_one()
        # Validation
        if sheet.state not in ("done", "post"):
            raise UserError(_("Only posted or paid expense report can create JV"))
        if sheet.wht_move_id:
            raise UserError(_("Already created withholding tax JV"))
        # Window action
        action = self.env.ref("account.action_move_journal_line")
        result = action.sudo().read()[0]
        view = self.env.ref("account.view_move_form", False)
        result["views"] = [(view and view.id or False, "form")]
        # Create wht JV
        move_vals = sheet._prepare_withholding_tax_entry()
        move = self.env["account.move"].create(move_vals)
        sheet.wht_move_id = move
        result["res_id"] = move.id
        return result

    def _prepare_withholding_tax_entry(self):
        self.ensure_one()
        # Prepare Dr. Advance, Cr. WHT lines
        line_vals_list = []
        move_lines = self.account_move_id.mapped("line_ids")
        # Cr. WHT Lines
        wht_move_lines = move_lines.filtered("wht_tax_id")
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
                    "wht_tax_id": deduction["wht_tax_id"],
                    "tax_base_amount": deduction["wht_amount_base"],
                }
            )
        accounts = move_lines.mapped("account_id").filtered("reconcile")
        # Dr. Reconcilable Account (i.e., AP, Advance)
        partner_id = self.employee_id.sudo().address_home_id.commercial_partner_id.id
        for account in accounts:
            line_vals_list.append(
                {
                    "name": account.name,
                    "amount_currency": amount_deduct,
                    "currency_id": currency.id,
                    "debit": amount_deduct,  # Sum of all credit
                    "credit": 0.0,
                    "partner_id": partner_id,
                    "account_id": account.id,
                }
            )
            amount_deduct = 0.0
        # Create JV
        move_vals = {
            "move_type": "entry",
            "ref": self.account_move_id.display_name,
            "line_ids": [(0, 0, line_vals) for line_vals in line_vals_list],
        }
        return move_vals
