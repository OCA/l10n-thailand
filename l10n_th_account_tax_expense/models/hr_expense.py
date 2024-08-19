# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    bill_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor",
        tracking=True,
    )
    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WHT",
        compute="_compute_wht_tax_id",
        store=True,
        readonly=False,
        tracking=True,
    )

    @api.onchange("tax_ids", "wht_tax_id")
    def _onchange_tax(self):
        self.bill_partner_id = False

    @api.depends("product_id")
    def _compute_wht_tax_id(self):
        for rec in self:
            rec.wht_tax_id = rec.product_id.supplier_wht_tax_id or False

    def _prepare_move_line_vals(self):
        """Add WHT in move line"""
        ml_vals = super()._prepare_move_line_vals()
        ml_vals["wht_tax_id"] = self.wht_tax_id.id
        return ml_vals

    def _get_move_line_src(self, move_line_name, partner_id):
        ml_src_dict = super()._get_move_line_src(move_line_name, partner_id)
        ml_src_dict["wht_tax_id"] = self.wht_tax_id.id
        return ml_src_dict
