# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetRemove(models.TransientModel):
    _inherit = "account.asset.remove"

    remove_reason = fields.Char(string="Removed Reason")

    def remove(self):
        res = super().remove()
        asset_ids = self.env.context.get("active_ids", [])
        assets = self.env["account.asset"].browse(asset_ids)
        assets.write({"remove_reason": self.remove_reason})
        return res

    def remove_multi_assets(self):
        asset_ids = self.env.context.get("active_ids", [])
        assets = self.env["account.asset"].browse(asset_ids)
        ctx = dict(self.env.context)
        for asset in assets:
            if (
                asset.method in ["linear-limit", "degr-limit"]
                and asset.value_residual != asset.salvage_value
                or asset.value_residual
            ):
                ctx.update({"early_removal": True})
            ctx.update({"active_id": asset.id})
            self.with_context(**ctx).remove()
        return True
