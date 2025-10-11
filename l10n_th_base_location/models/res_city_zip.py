# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResCityZip(models.Model):
    _inherit = "res.city.zip"
    _rec_names_search = ["name", "subdistrict_id", "city_id", "state_id", "country_id"]

    _sql_constraints = [
        (
            "name_city_uniq",
            "UNIQUE(name, subdistrict_id, city_id)",
            "You already have a zip with that code in the same city. "
            "The zip code must be unique within it's city",
        )
    ]

    subdistrict_id = fields.Many2one(
        comodel_name="res.subdistrict",
        string="Sub-District",
        auto_join=True,
        ondelete="cascade",
        index=True,
    )

    @api.depends(
        "name",
        "subdistrict_id",
        "city_id",
        "city_id.name",
        "city_id.state_id.name",
        "city_id.state_id",
        "city_id.country_id",
        "city_id.country_id.name",
    )
    def _compute_display_name(self):
        """
        Get the proper display name formatted as
        'ZIP, Sub-District, District (City), state, country'.
        """
        for rec in self:
            state_name = (
                rec.city_id.state_id.name + ", " if rec.city_id.state_id else ""
            )
            country_name = rec.city_id.country_id.name if rec.city_id.country_id else ""
            subdistrict = rec.subdistrict_id.name
            district = rec.city_id.name
            zipcode = rec.name
            rec.display_name = (
                f"{zipcode}, {subdistrict}, {district}, {state_name}{country_name}"
            )
