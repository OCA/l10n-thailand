# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    expense_sheet_ids = fields.One2many(
        comodel_name="hr.expense.sheet",
        inverse_name="purchase_request_id",
        string="Expense Report",
    )
    expense_sheet_count = fields.Integer(
        string="Expense Report Count",
        compute="_compute_expense_sheet_count",
    )

    @api.depends("expense_sheet_ids")
    def _compute_expense_sheet_count(self):
        for rec in self:
            rec.expense_sheet_count = len(rec.expense_sheet_ids)

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

    def button_draft(self):
        for rec in self:
            if any(sheet.state != "cancel" for sheet in rec.expense_sheet_ids):
                raise UserError(
                    _(
                        "The PR is already associated with an Expense. "
                        "Please cancel the Expense before proceeding."
                    )
                )
        return super().button_draft()

    def button_rejected(self):
        for rec in self:
            if any(sheet.state != "cancel" for sheet in rec.expense_sheet_ids):
                raise UserError(
                    _(
                        "The PR is already associated with an Expense. "
                        "Please cancel the Expense before proceeding."
                    )
                )
        return super().button_rejected()
