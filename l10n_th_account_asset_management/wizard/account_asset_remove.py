# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetRemove(models.TransientModel):
    _inherit = "account.asset.remove"

    asset_sub_state_id = fields.Many2one(
        comodel_name="account.asset.sub.state",
        string="Sub-Status",
        domain="[('removed', '=', True), '|', ('company_id', '=', False), "
        "('company_id', '=', company_id)]",
        default=lambda self: self.env["account.asset.sub.state"].search(
            [
                ("removed", "=", True),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        ),
        check_company=True,
    )

    def remove(self):
        res = super().remove()
        asset_ids = self.env.context.get("active_ids", [])
        assets = self.env["account.asset"].browse(asset_ids)
        asset_sub_state = self.asset_sub_state_id
        if not asset_sub_state:
            asset_sub_state = self.env["account.asset.sub.state"].search(
                [
                    ("removed", "=", True),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
        if asset_sub_state:
            assets.write({"asset_sub_state_id": asset_sub_state.id})
        return res
