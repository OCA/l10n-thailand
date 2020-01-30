# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ResTambon(models.Model):
    _name = "res.tambon"
    _description = "Tambon/Khwaeng"

    name = fields.Char(string="Tambon/Khwaeng Name")
    name_eng = fields.Char(string="Tambon/Khwaeng Name English")
    amphur_id = fields.Many2one("res.amphur", string="Amphur/Khet")
    zip_ids = fields.One2many("res.zip", "tambon_id", string="Zip Code")
