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

    def _get_removal_data(self, asset, residual_value):
        move_lines = super()._get_removal_data(asset, residual_value)
        if self.env.company.asset_move_line_analytic:
            analytic_account = asset.account_analytic_id.id
            analytic_tags = [(4, tag.id) for tag in asset.analytic_tag_ids]
            move_lines = [
                (
                    ml[0],
                    ml[1],
                    {
                        **ml[2],
                        "analytic_account_id": analytic_account,
                        "analytic_tag_ids": analytic_tags,
                    },
                )
                for ml in move_lines
            ]
        return move_lines
