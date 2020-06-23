# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import csv
import os

from odoo import api, fields, models


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    is_thailand = fields.Boolean(
        compute="_compute_is_thailand",
        readonly=True,
        help="For Thailand only, data is from TH_th.txt and TH_en.txt stored "
        "in the module's data folder. To get data from Geonames.org, "
        "please uninstall l10n_th_base_location.",
    )
    location_thailand_language = fields.Selection(
        [("th", "Thai"), ("en", "English")], string="Language of Thailand", default="th"
    )

    @api.depends("country_ids")
    def _compute_is_thailand(self):
        self.ensure_one()
        self.is_thailand = "TH" in self.country_ids.mapped("code")

    def _prepare_district_thailand(self, row):
        sub_district = ""
        district = ""
        if len(row) >= 6:
            district = row[5]
            if len(row) >= 7:
                sub_district = row[6]
        return district, sub_district

    @api.model
    def prepare_zip(self, row, city_id):
        vals = super().prepare_zip(row, city_id)
        district, sub_district = self._prepare_district_thailand(row)
        vals.update({"district_code": district, "sub_district_code": sub_district})
        return vals

    @api.model
    def select_zip(self, row, country, state_id):
        city_zip = super().select_zip(row, country, state_id)
        if country.code == "TH":
            # If District or Sub-District, update code
            district, sub_district = self._prepare_district_thailand(row)
            city_zip.write(
                {"district_code": district, "sub_district_code": sub_district}
            )
        return city_zip

    @api.model
    def get_and_parse_csv(self, country):
        if country.code == "TH":
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
            import_test = self._context.get("import_test", False)
            if import_test:
                th_location_file = "demo/TH_th.txt"
                en_location_file = "demo/TH_en.txt"
            else:
                th_location_file = "data/TH_th.txt"
                en_location_file = "data/TH_en.txt"
            if self.location_thailand_language == "th":
                file_path = os.path.join(path[:-6], th_location_file)
            else:
                file_path = os.path.join(path[:-6], en_location_file)
            data_file = open(file_path, "r", encoding="utf-8")
            data_file.seek(0)
            reader = csv.reader(data_file, delimiter="	")
            parsed_csv = [row for i, row in enumerate(reader)]
            data_file.close()
            return parsed_csv
        return super().get_and_parse_csv(country)
