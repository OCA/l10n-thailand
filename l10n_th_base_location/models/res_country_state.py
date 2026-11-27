# Copyright 2021 Sansiri Tanachutiwat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class CountryState(models.Model):
    _inherit = "res.country.state"

    prefix = fields.Char()
    short_prefix = fields.Char()

    @api.depends("name", "country_id")
    def _compute_display_name(self):
        for rec in self:
            if rec.country_id.code == "TH":
                rec.display_name = rec.name
            else:
                super(CountryState, rec)._compute_display_name()
        return
