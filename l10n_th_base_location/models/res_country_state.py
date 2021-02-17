# -*- coding: utf-8 -*-

from odoo import models

class CountryState(models.Model):
    _inherit = 'res.country.state'

    def name_get(self):
        result = []
        for record in self:
            if record.country_id.code == "TH":
                result.append((record.id, record.name))
            else:
                result.append((record.id, "{} ({})".format(record.name, record.country_id.code)))
        return result
