# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("zip_id")
    def _compute_city(self):
        super()._compute_city()
        for record in self:
            if record.zip_id and record.country_id.code == "TH":
                address = record.zip_id.city_id.name.split(", ")
                record.update({"street2": address[0], "city": address[1]})
