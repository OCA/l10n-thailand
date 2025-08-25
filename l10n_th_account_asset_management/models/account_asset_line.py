# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    def create_move(self):
        created_move_ids = super().create_move()
        assets = self.mapped("asset_id")
        to_close = assets.filtered(
            lambda a: a.company_currency_id.compare_amounts(
                a.value_residual, a.salvage_value
            )
            == 0
        )
        if to_close:
            to_close.write({"state": "close"})
        return created_move_ids
