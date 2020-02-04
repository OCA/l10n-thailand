# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _get_computed_name(self, lastname, firstname):
        name = super()._get_computed_name(lastname, firstname)
        title = self.title.name
        if name and title:
            return " ".join(p for p in (title, name) if p)
        return name

    @api.depends("title", "firstname", "lastname")
    def _compute_name(self):
        return super()._compute_name()

    @api.onchange("company_type")
    def _onchange_company_type(self):
        if self.company_type == "company":
            self.title = False
