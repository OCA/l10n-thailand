# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    branch = fields.Char(
        related="partner_id.branch", string="Tax Branch", readonly=False
    )
    no_space_title_name = fields.Boolean(
        string="No Space Title and Name",
        help="If checked, title and name will no space",
    )

    def write(self, vals):
        """Automation update name when you config no_space_title_name"""
        res = super().write(vals)
        if "no_space_title_name" in vals:
            personal_partners = (
                self.env["res.partner"]
                .search([("title", "!=", False)])
                .with_context(skip_inverse_name=True)
            )
            for partner in personal_partners:
                partner.name = partner._get_computed_name(
                    partner.lastname, partner.firstname
                )
        return res
