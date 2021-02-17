# Copyright 2021 Sansiri Tanachutiwat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class CountryState(models.Model):
    _inherit = "res.country.state"

    def name_get(self):
        result = []
        for record in self:
            if record.country_id.code == "TH":
                result.append((record.id, record.name))
            else:
                result.append(super(CountryState, record).name_get()[0])
        return result
