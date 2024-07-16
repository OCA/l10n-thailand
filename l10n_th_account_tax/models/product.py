# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Withholding Tax",
        company_dependent=True,
        domain="[('company_id', '=', current_company_id)]",
        help="Default withholding tax for the customer",
    )
    supplier_wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Individual Vendor Withholding Tax",
        company_dependent=True,
        domain="[('company_id', '=', current_company_id)]",
        help="Default withholding tax for the vendor that is individual",
    )
    supplier_company_wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Company Vendor Withholding Tax",
        company_dependent=True,
        domain="[('company_id', '=', current_company_id)]",
        help="Default withholding tax for the vendor that is company",
    )
