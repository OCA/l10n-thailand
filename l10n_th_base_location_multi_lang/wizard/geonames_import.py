# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    def _process_csv(self, parsed_csv, country):
        res = super()._process_csv(parsed_csv, country)
        if country.code == "TH":
            self.env["res.city.zip"]._load_thailand_name_en()
        return res
