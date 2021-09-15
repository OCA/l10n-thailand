# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    def create_move(self):
        created_move_ids = super().create_move()
        assets = self.mapped("asset_id")
        for asset in assets:
            if (
                asset.company_currency_id.compare_amounts(
                    asset.value_residual, asset.salvage_value
                )
                == 0
            ):
                asset.state = "close"
        return created_move_ids
