# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WT",
        compute="_compute_wt_tax_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "account_id")
    def _compute_wt_tax_id(self):
        for rec in self:
            rec.wt_tax_id = rec.product_id.supplier_wt_tax_id or False

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense in self:
            wt_tax_dict = {"wt_tax_id": expense.wt_tax_id.id}
            for ml in move_line_values_by_expense[expense.id]:
                if ml.get("product_id"):
                    ml.update(wt_tax_dict)
        return move_line_values_by_expense
