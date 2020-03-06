# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _inverse_street2(self):
        return super(
            ResCompany, self.with_context(skip_check_zip=True)
        )._inverse_street2()

    @api.onchange("zip_id")
    def _onchange_zip_id(self):
        res = super()._onchange_zip_id()
        if self.zip_id and self.country_id.code == "TH":
            address = self.zip_id.city_id.name.split(", ")
            self.update({"street2": address[0], "city": address[1]})
        return res
