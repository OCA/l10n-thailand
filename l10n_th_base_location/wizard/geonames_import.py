# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import csv
import logging
import os

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    is_thailand = fields.Boolean(
        compute="_compute_is_thailand",
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
        row_dict = dict(enumerate(row))
        district = row_dict.get(5, "")
        sub_district = row_dict.get(6, "")
        return district, sub_district

    @api.model
    def prepare_zip(self, row, city_id):
        """Add district_code and sub_district_code into vals"""
        vals = super().prepare_zip(row, city_id)
        district, sub_district = self._prepare_district_thailand(row)
        vals.update({"district_code": district, "sub_district_code": sub_district})
        return vals

    def _create_states(self, parsed_csv, search_states, max_import, country):
        """In the core Odoo system, Thailand's provinces already exist.
        This function updates the names to TH/EN for states."""
        if country.code == "TH":
            states_map = {}
            if search_states:
                states_map = {
                    state.code: state
                    for state in self.env["res.country.state"].search(
                        [("country_id", "=", country.id)]
                    )
                }
            # States
            state_vals_set = set()
            state_dict = {}
            for i, row in enumerate(parsed_csv):
                if max_import and i == max_import:
                    break
                state = None
                if search_states:
                    code = row[country.geonames_state_code_column or 4]
                    state = states_map.get(code)
                state_vals = self.prepare_state(row, country)
                if not state:
                    state_vals_set.add(
                        (
                            state_vals["name"],
                            state_vals["code"],
                            state_vals["country_id"],
                        )
                    )
                # Update name
                else:
                    state.write({"name": state_vals["name"]})
                    state_dict[state.code] = state
            state_vals_list = [
                {"name": name, "code": code, "country_id": country_id}
                for name, code, country_id in state_vals_set
            ]
            logger.info("Importing %d states", len(state_vals_list))
            created_states = self.env["res.country.state"].create(state_vals_list)
            for i, vals in enumerate(state_vals_list):
                state_dict[vals["code"]] = created_states[i]
            return state_dict
        return super()._create_states(parsed_csv, search_states, max_import, country)

    @api.model
    def get_and_parse_csv(self, country):
        if country.code == "TH":
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
            # th_location_file = "demo/TH_th.txt" if import_test else "data/TH_th.txt"
            # en_location_file = "demo/TH_en.txt" if import_test else "data/TH_en.txt"
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
