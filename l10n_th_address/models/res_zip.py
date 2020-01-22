# -*- coding: utf-8 -*-
# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models, _


class ResZip(models.Model):
    _name = "res.zip"
    _description = "Zip"

    name = fields.Char(
        string="Zip Code",
    )
    tambon_id = fields.Many2one(
        "res.tambon",
        string="Tambon",
    )
