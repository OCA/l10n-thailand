# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetTransfer(models.TransientModel):
    _inherit = "account.asset.transfer"

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

    def transfer(self):
        res = super().transfer()
        if self.asset_sub_state_id:
            self.from_asset_ids.write(
                {"asset_sub_state_id": self.asset_sub_state_id.id}
            )
        return res
