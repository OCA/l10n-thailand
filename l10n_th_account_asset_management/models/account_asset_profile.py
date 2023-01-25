# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetProfile(models.Model):
    _inherit = "account.asset.profile"

    salvage_value = fields.Float(
        string="Salvage Value",
        digits="Account",
        default=1.0,
    )
