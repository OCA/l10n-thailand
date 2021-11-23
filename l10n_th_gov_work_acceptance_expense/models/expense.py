# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class HRExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    purchase_request_id = fields.Many2one(
        domain="[('requested_by', '=', employee_user_id),"
        "('state', '=', 'approved'), ('to_create', '=', 'expense')]",
    )

    def action_submit_sheet(self):
        self._validate_purchase_request()
        self._validate_work_acceptance()
        return super().action_submit_sheet()

    def approve_expense_sheets(self):
        self._validate_purchase_request()
        self._validate_work_acceptance()
        return super().approve_expense_sheets()

    def _validate_purchase_request(self):
        purchase_requests = self.mapped("purchase_request_id")
        for pr in purchase_requests:
            if pr.purchase_type_id.to_create != "expense":
                raise UserError(_("Selected purchase request is not for expense!"))

    def _validate_work_acceptance(self):
        if not self.env.user.has_group(
            "hr_expense_work_acceptance.group_enable_wa_on_exp"
        ):
            return
        sheets = self.filtered(lambda l: l.purchase_request_id and not l.advance)
        if sheets.filtered(lambda l: not l.wa_accepted):
            raise UserError(_("WA is not yet accepted!"))