# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HRExpenseSheet(models.Model):
    _name = "hr.expense.sheet"
    _inherit = ["hr.expense.sheet", "base.cosmetic.vat"]
    _line_field = "expense_line_ids"
    _partner_field = "employee_id.user_partner_id"

    @api.onchange("employee_id")
    def _onchange_cosmetic_vat(self):
        super()._onchange_cosmetic_vat()


class HRExpense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "base.cosmetic.vat.line"]
    _inverse_field = "sheet_id"
    _price_field = "unit_amount"
    _subtotal_field = "total_amount"
    _quantity_field = "quantity"

    cosmetic_vat = fields.Integer(
        related="sheet_id.cosmetic_vat",
    )

    @api.onchange("quantity", "unit_amount")
    def _onchange_cosmetic_product_qty(self):
        super()._onchange_cosmetic_product_qty()

    @api.depends("cosmetic_price_unit", "quantity")
    def _compute_cosmetic_subtotal(self):
        super()._compute_cosmetic_subtotal()

    def _create_sheet_from_expenses(self):
        sheet = super()._create_sheet_from_expenses()
        sheet._onchange_cosmetic_vat()
        return sheet

    def apply_cosmetic_vat(self):
        for rec in self.filtered(lambda l: not l.set_cosmetic_vat):
            rec.whtvat = rec.cosmetic_vat
        return super().apply_cosmetic_vat()
