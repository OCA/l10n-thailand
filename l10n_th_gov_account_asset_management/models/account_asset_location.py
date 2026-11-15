# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetLocation(models.Model):
    _name = "account.asset.location"
    _description = "Asset Location"

    name = fields.Char()
    active = fields.Boolean(default=True)
