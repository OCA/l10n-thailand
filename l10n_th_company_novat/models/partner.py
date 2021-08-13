# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    def map_tax(self, taxes, product=None, partner=None):
        """ For non-VAT company, always result with no taxes """
        if self.env.company.novat or (partner and partner.novat):
            return self.env["account.tax"]
        return super().map_tax(taxes, product=product, partner=partner)


class ResPartner(models.Model):
    _inherit = "res.partner"

    novat = fields.Boolean(
        string="Not VAT Registered",
        help="This partner is not a vat registered vendor/customer. "
        "Odoo will try to remove taxes from document",
    )
