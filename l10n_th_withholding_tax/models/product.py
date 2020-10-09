# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    wt_tax_id = fields.Many2one(comodel_name="account.withholding.tax")
    supplier_wt_tax_id = fields.Many2one(comodel_name="account.withholding.tax")
