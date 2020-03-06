# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange("zip_id")
    def _onchange_zip_id(self):
        res = super()._onchange_zip_id()
        if self.zip_id and self.country_id.code == "TH":
            address = self.zip_id.city_id.name.split(", ")
            self.update({"street2": address[0], "city": address[1]})
        return res
