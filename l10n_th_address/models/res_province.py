# -*- coding: utf-8 -*-
# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models, _


class ResProvince(models.Model):
    _name = "res.province"
    _description = "Province"

    name = fields.Char(
        string="Province Name",
    )
    name_eng = fields.Char(
        string="Province Name English",
    )
    code = fields.Char(
        string="Code",
    )
    amphur_ids = fields.One2many(
        "res.amphur",
        "province_id",
        string="Amphurs/Khets"
    )
