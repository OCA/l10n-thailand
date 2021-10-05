# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    name = fields.Char(
        translate=True,
    )
