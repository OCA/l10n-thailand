# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAssetTransfer(models.TransientModel):
    _inherit = "account.asset.transfer"

    def _get_new_move_transfer(self):
        res = super()._get_new_move_transfer()
        from_asset_number = [
            asset.number for asset in self.from_asset_ids if asset.number
        ]
        if from_asset_number:
            res["ref"] = ", ".join(from_asset_number)
        return res

    def _get_move_line_from_asset(self, asset):
        res = super()._get_move_line_from_asset(asset)
        asset_id = res.get("asset_id", False)
        if asset_id:
            asset = self.env["account.asset"].browse(asset_id)
            res["name"] = asset.display_name
        return res
