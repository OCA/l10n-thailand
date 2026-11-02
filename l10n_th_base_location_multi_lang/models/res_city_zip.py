# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import csv

from odoo import api, fields, models
from odoo.modules.module import get_module_resource


class ResCityZip(models.Model):
    _inherit = "res.city.zip"

    subdistrict_en = fields.Char(string="Sub-District (EN)")
    district_en = fields.Char(string="District (EN)")
    state_en = fields.Char(string="State (EN)")

    @api.model
    def _load_thailand_name_en(self):
        path = get_module_resource("l10n_th_base_location", "data", "TH_en.txt")
        with open(path, encoding="utf-8") as data_file:
            rows = {
                row[6]: row
                for row in csv.reader(data_file, delimiter="\t")
                if len(row) >= 7
            }
        city_zips = self.search(
            [
                ("city_id.country_id.code", "=", "TH"),
                ("sub_district_code", "in", list(rows)),
            ]
        )
        for city_zip in city_zips:
            row = rows[city_zip.sub_district_code]
            subdistrict, _sep, district = row[2].partition(",")
            city_zip.write(
                {
                    "subdistrict_en": subdistrict.strip(),
                    "district_en": district.strip(),
                    "state_en": row[3],
                }
            )
        return True
