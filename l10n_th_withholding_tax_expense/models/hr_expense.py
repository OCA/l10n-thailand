# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class HRExpense(models.Model):
    _inherit = "hr.expense"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WT",
        compute="_compute_wt_tax_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_wt_tax_id(self):
        for expense in self:
            expense.wt_tax_id = expense.product_id.supplier_wt_tax_id
