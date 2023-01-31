# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    expense_sheet_ids = fields.One2many(
        comodel_name="hr.expense.sheet",
        compute="_compute_expense_sheet_count",
        string="Expense Report",
    )
    expense_sheet_count = fields.Integer(
        string="Expense Report Count",
        compute="_compute_expense_sheet_count",
    )

    def _compute_expense_sheet_count(self):
        for move in self:
            move.expense_sheet_ids = move.line_ids.mapped("expense_id").mapped(
                "sheet_id"
            )
            move.expense_sheet_count = len(move.expense_sheet_ids)

    def action_view_expense_sheet(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "hr_expense.action_hr_expense_sheet_my_all"
        )
        expense_sheets = self.expense_sheet_ids
        if len(expense_sheets) > 1:
            action["domain"] = [("id", "in", expense_sheets.ids)]
        elif expense_sheets:
            action["views"] = [
                (self.env.ref("hr_expense.view_hr_expense_sheet_form").id, "form")
            ]
            action["res_id"] = expense_sheets[0].id
        return action
