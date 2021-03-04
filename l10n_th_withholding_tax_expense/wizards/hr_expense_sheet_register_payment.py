# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.sheet.register.payment.wizard"

    wt_tax_id = fields.Many2one(
        string="Withholding Tax",
        comodel_name="account.withholding.tax",
        help="Optional hidden field to keep wt_tax. Useful for case 1 tax only",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if not res.get("expense_sheet_id", False):
            return res
        if self._context.get("active_id"):
            sheet = self.env["hr.expense.sheet"].browse(self._context["active_id"])
            expenses = sheet.expense_line_ids.filtered("wt_tax_id")
            amount_wt = sum(
                expenses.mapped(lambda l: l.wt_tax_id.amount / 100 * l.untaxed_amount)
            )
            if amount_wt:
                res["amount"] -= amount_wt
                res["payment_difference_handling"] = "reconcile"
                wt_tax = expenses.mapped("wt_tax_id")
                if wt_tax and len(wt_tax) == 1:
                    res["wt_tax_id"] = wt_tax.id
        return res

    @api.onchange("wt_tax_id")
    def _onchange_wt_tax_id(self):
        if self.wt_tax_id:
            self.writeoff_account_id = self.wt_tax_id.account_id
            self.writeoff_label = self.wt_tax_id.display_name
