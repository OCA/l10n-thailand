# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SubDistrict(models.Model):
    _name = "res.subdistrict"
    _description = "Sub-District"
    _rec_names_search = ["name", "city_id"]

    _sql_constraints = [
        (
            "subdistrict_name_city_uniq",
            "unique(name, code, city_id)",
            "You already have a subdistrict with that name in the same city."
            "The subdistrict must have a unique name within "
            "it's city and it's country",
        )
    ]

    name = fields.Char(required=True, translate=True)
    code = fields.Char(index=True)
    city_id = fields.Many2one(comodel_name="res.city", required=True, index=True)
    zipcode = fields.Char(string="Zip")
    prefix = fields.Char()
    short_prefix = fields.Char()
