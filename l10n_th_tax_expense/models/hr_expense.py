# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    bill_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor",
    )
    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WHT",
        compute="_compute_wht_tax_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "account_id")
    def _compute_wht_tax_id(self):
        for rec in self:
            rec.wht_tax_id = rec.product_id.supplier_wht_tax_id or False

    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        # Set wht_tax_id, to account move line
        for expense in self:
            wht_tax_dict = {"wht_tax_id": expense.wht_tax_id.id}
            for ml in move_line_values_by_expense[expense.id]:
                if ml.get("product_id"):
                    ml.update(wht_tax_dict)
        # Set tax_exigible, to ensure that, tax inovice is not created for undue vat
        RepartTax = self.env["account.tax.repartition.line"]
        for move_lines in move_line_values_by_expense.values():
            for move_line in filter(
                lambda l: l.get("tax_repartition_line_id"), move_lines
            ):
                tax = RepartTax.browse(move_line["tax_repartition_line_id"]).tax_id
                move_line["tax_exigible"] = tax.tax_exigibility == "on_invoice"
        return move_line_values_by_expense
