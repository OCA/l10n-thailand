# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    novat = fields.Boolean(
        string="Not VAT Registered",
        help="If checked, all documents must not contain any VAT",
    )


class BaseCompanyNoVAT(models.AbstractModel):
    _name = "base.company.novat"
    _description = "Base Company NoVAT"
    _tax_field_name = "tax_ids"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if (
            self.env.company.novat
            and self._tax_field_name in vals
            and res.mapped(self._tax_field_name)
        ):
            raise UserError(
                _("Taxes not allowed for Non-VAT registered company, %s")
                % self.env.company.display_name
            )
        return res

    def write(self, vals):
        res = super().write(vals)
        if (
            self.env.company.novat
            and self._tax_field_name in vals
            and self.mapped(self._tax_field_name)
        ):
            raise UserError(
                _("Taxes not allowed for Non-VAT registered company, %s")
                % self.env.company.display_name
            )
        return res
