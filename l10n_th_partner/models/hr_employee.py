# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    name = fields.Char(translate=True)
