# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class Expense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "base.company.novat"]
    _tax_field_name = "tax_ids"

    whtvat = fields.Float(
        string="Vat%",
        compute="_compute_whtvat",
        store=True,
        copy=True,
        readonly=False,
        help="Only with No-VAT registered company, set default tax  "
        "to calculate base amount used for withholding amount",
    )

    @api.depends("employee_id")
    def _compute_whtvat(self):
        if not self.env.company.novat:
            self.update({"whtvat": False})
            return
        for rec in self:
            partner = rec.employee_id.address_home_id
            percent = False
            if partner and not partner.novat:  # VAT partner
                percent = self.env.company.account_purchase_tax_id.amount
            rec.whtvat = percent

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense in self:
            whtvat_dict = {"whtvat": expense.whtvat}
            for ml in move_line_values_by_expense[expense.id]:
                if ml.get("product_id"):
                    ml.update(whtvat_dict)
        return move_line_values_by_expense
