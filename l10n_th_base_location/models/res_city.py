# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class City(models.Model):
    _inherit = "res.city"

    _sql_constraints = [
        (
            "name_state_country_uniq",
            "UNIQUE(name, code, state_id, country_id)",
            "You already have a city with that name in the same state."
            "The city must have a unique name within "
            "it's state and it's country",
        )
    ]

    code = fields.Char(index=True)
    subdistrict_ids = fields.One2many(
        comodel_name="res.subdistrict",
        inverse_name="city_id",
        string="Sub-District",
    )
