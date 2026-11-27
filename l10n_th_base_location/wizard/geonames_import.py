# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import csv
import logging
from collections import defaultdict

from odoo import api, models
from odoo.tools import file_open

logger = logging.getLogger(__name__)


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

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

    def _action_remove_old_records(self, model_name, old_records, country):
        """Case: import again, it must remove subdistrict first"""
        ctx = {}
        if model_name == "res.city" and not self.env.context.get("rm_subdistrict"):
            cities = self.env["res.city"].browse(list(old_records))
            cities.mapped("subdistrict_ids").unlink()
            ctx = {"rm_subdistrict": 1}
        return super(
            CityZipGeonamesImport, self.with_context(**ctx)
        )._action_remove_old_records(model_name, old_records, country)

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
                    "prefix": row[8],
                    "short_prefix": row[11] if len(row) > 11 else "",
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
        if country.code != "TH":
            return super().get_and_parse_csv(country)
        with file_open("l10n_th_base_location/data/th_subdistrict.csv") as f:
            data = list(csv.DictReader(f))
        parsed_csv = []
        for key, lang in (("TH", "th"), ("EN", "en")):
            is_th = key == "TH"
            parsed_csv += [
                [
                    "TH",
                    row["zip"],
                    row[f"district_{lang}"],
                    row[f"province_{lang}"],
                    f"{key}-{row['subdistrict_code'][:2]}",
                    row[f"subdistrict_{lang}"],
                    row["subdistrict_code"],
                    row["district_code"],
                    row[f"subdistrict_prefix_{lang}"],
                    row[f"district_prefix_{lang}"],
                    row[f"province_prefix_{lang}"],
                    row["subdistrict_short_prefix"] if is_th else "",
                    row["district_short_prefix"] if is_th else "",
                    row["province_short_prefix"] if is_th else "",
                    key,
                ]
                for row in data
            ]
        return parsed_csv

    def _process_csv(self, parsed_csv, country):
        res = super()._process_csv(parsed_csv, country)
        if country.code != "TH":
            return res
        for row in parsed_csv:
            if len(row) < 11:
                continue
            is_th_pass = len(row) > 14 and row[14] == "TH"
            state = self.env["res.country.state"].search(
                [
                    ("code", "=", row[country.geonames_state_code_column or 4]),
                    ("country_id", "=", country.id),
                ],
                limit=1,
            )
            if not state:
                continue
            if row[10]:
                state.prefix = row[10]
            if is_th_pass and len(row) > 13 and row[13]:
                state.short_prefix = row[13]
            city = self.env["res.city"].search(
                [
                    ("name", "=", self.transform_city_name(row[2], country)),
                    ("state_id", "=", state.id),
                ],
                limit=1,
            )
            if city and row[9]:
                city.prefix = row[9]
            if is_th_pass and city and len(row) > 12 and row[12]:
                city.short_prefix = row[12]
            if city and row[8]:
                zip_rec = self.env["res.city.zip"].search(
                    [
                        ("name", "=", row[1]),
                        ("city_id", "=", city.id),
                    ]
                )
                if zip_rec:
                    zip_rec.prefix = row[8]
                    if is_th_pass and len(row) > 11 and row[11]:
                        zip_rec.short_prefix = row[11]
        return res
