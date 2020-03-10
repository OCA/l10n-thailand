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
        [("th", "Thai"), ("en", "English")], string="Language", default="th"
    )

    @api.depends("country_id")
    def _compute_is_thailand(self):
        self.ensure_one()
        self.is_thailand = self.country_id.code == "TH"

    @api.model
    def get_and_parse_csv(self):
        if self.is_thailand:
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
