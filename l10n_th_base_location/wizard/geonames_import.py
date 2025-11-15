# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
from collections import defaultdict

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

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

    @api.model
    def prepare_zip(self, row, city_id):
        """Add district_code and sub_district_code into vals"""
        vals = super().prepare_zip(row, city_id)
        subdistrict = self.env["res.subdistrict"].search(
            [("code", "=", row[6]), ("city_id", "=", city_id)]
        )
        vals.update({"subdistrict_id": subdistrict.id})
        return vals

    @api.model
    def prepare_city_th(self, row, country, state):
        vals = {
            "name": self.transform_city_name(row[2], country),
            "state_id": state.id,
            "country_id": country.id,
            "code": row[7],
        }
        return vals

    def _create_subdistrict_th(self, subdistrict_list):
        created_subdistricts = self.env["res.subdistrict"].create(subdistrict_list)
        return created_subdistricts

    @api.model
    def _search_subdistrict(self, row):
        return self.env["res.subdistrict"].search(
            [
                ("name", "=", row[5]),
                ("code", "=", row[6]),
                ("zipcode", "=", row[1]),
            ],
            limit=1,
        )

    def _create_cities(
        self, parsed_csv, search_cities, max_import, state_dict, country
    ):
        if country.code != "TH":
            return super()._create_cities(
                parsed_csv, search_cities, max_import, state_dict, country
            )

        # Subdistrict
        pending_subdistricts = defaultdict(list)
        subdistrict_list = []

        # Cities
        city_vals_set = set()
        city_dict = {}
        for i, row in enumerate(parsed_csv):
            if max_import and i == max_import:
                break
            state = state_dict[row[country.geonames_state_code_column or 4]]
            city = (
                self._select_city(row, country, state)
                if search_cities
                else self.env["res.city"]
            )

            # Not Found subdistrict, Create new
            subdistrict = self._search_subdistrict(row)
            if not subdistrict:
                subdistrict_data = {
                    "name": row[5],
                    "code": row[6],
                    "zipcode": row[1],
                }
            if not city:
                city_vals = self.prepare_city_th(row, country, state)
                city_key = (city_vals["name"], city_vals["state_id"])
                city_vals_set.add(
                    (
                        city_vals["name"],
                        city_vals["state_id"],
                        city_vals["country_id"],
                        city_vals["code"],
                    )
                )
                if not subdistrict:
                    pending_subdistricts[city_key].append(subdistrict_data)
            else:
                city_dict[(city.name, state.id)] = city.id
                if not subdistrict:
                    subdistrict_data["city_id"] = city.id
                    subdistrict_list.append(subdistrict_data)

        city_vals_list = [
            {"name": name, "state_id": state_id, "country_id": country_id, "code": code}
            for name, state_id, country_id, code in city_vals_set
        ]
        logger.info("Importing %d cities", len(city_vals_list))
        created_cities = self.env["res.city"].create(city_vals_list)
        for i, vals in enumerate(city_vals_list):
            city_dict[(vals["name"], vals["state_id"])] = created_cities[i].id

        # Add city in subdistrict (for case no city)
        for (city_name, state_id), subs in pending_subdistricts.items():
            city_id = city_dict.get((city_name, state_id))
            for sub in subs:
                sub["city_id"] = city_id
                subdistrict_list.append(sub)

        logger.info("Importing %d subdistricts", len(subdistrict_list))
        if subdistrict_list:
            self._create_subdistrict_th(subdistrict_list)
        return city_dict

    @api.model
    def get_and_parse_csv(self, country):
        if country.code == "TH":
            url = self.env["ir.config_parameter"].get_param("geonames.th.url")
            if not url:
                return super().get_and_parse_csv(country)

            res_request = requests.get(url, timeout=15)
            if res_request.status_code != requests.codes.ok:
                # pylint: disable=translation-positional-used - Don't want to re-translate
                raise UserError(
                    self.env._(
                        "Got an error %d when trying to download the file %s.",
                        res_request.status_code,
                        url,
                    )
                )

            json_data = res_request.json()
            # Standard Format is
            # - (1) Code Country
            # - (2) Zip Code
            # - (3) District (City)
            # - (4) State (Province)
            # - (5) State Code (Province Code)
            # For Thailand, we add subdistrict at row6
            # - (6) Sub-district
            # - (7) Sub-district Code
            # - (8) District Code (City Code)
            lang = "name_th" if self.location_thailand_language == "th" else "name_en"
            parsed_csv = [
                [
                    "TH",
                    data["zip_code"],
                    data["district"][lang],
                    data["district"]["province"][lang],
                    f"TH-{str(data['id'])[:2]}",
                    data[lang],
                    data["id"],
                    data["district"]["id"],
                ]
                for data in json_data
            ]
            return parsed_csv
        return super().get_and_parse_csv(country)
