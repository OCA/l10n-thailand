# -*- coding: utf-8 -*-
# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models, _


class ResAmphur(models.Model):
    _name = "res.amphur"
    _description = "Amphur/Khet"

    name = fields.Char(
        string="Amphur/Khet Name",
    )
    name_eng = fields.Char(
        string="Amphur/Khet Name English",
    )
    code = fields.Char(
        string="Code",
    )
    province_id = fields.Many2one(
        "res.province",
        string="Province",
    )
    tambon_ids = fields.One2many(
        "res.tambon",
        "amphur_id",
        string="Tambons/Khwaeng",
    )
