# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SubDistrict(models.Model):
    _name = "res.subdistrict"
    _description = "Sub-District"
    _rec_names_search = ["name", "city_id"]

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    city_id = fields.Many2one(comodel_name="res.city", required=True)
    zipcode = fields.Char(string="Zip")
