# Copyright 2021 Sansiri Tanachutiwat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class CountryState(models.Model):
    _inherit = "res.country.state"

    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("name", "country_id.code")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for record in self:
            if record.country_id.code == "TH":
                record.display_name = record.name
        return res
