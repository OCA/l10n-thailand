# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResBranch(models.Model):
    _inherit = "res.branch"

    operating_unit_ids = fields.Many2many(
        comodel_name="operating.unit",
    )
