# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import csv
import os

from odoo import api, fields, models


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    country_name = fields.Char(related="country_id.name", readonly=True)
    location_thailand_language = fields.Selection(
        [("th", "Thai"), ("en", "English")], string="Language", default="th"
    )

    @api.model
    def get_and_parse_csv(self):
        if self.country_id.name == "Thailand":
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
            if self.location_thailand_language == "th":
                file_path = os.path.join(path[:-6], "data/TH_th.txt")
            else:
                file_path = os.path.join(path[:-6], "data/TH_en.txt")
            data_file = open(file_path, "r", encoding="utf-8")
            data_file.seek(0)
            reader = csv.reader(data_file, delimiter="	")
            parsed_csv = [row for i, row in enumerate(reader)]
            data_file.close()
            return parsed_csv
        return super().get_and_parse_csv()
