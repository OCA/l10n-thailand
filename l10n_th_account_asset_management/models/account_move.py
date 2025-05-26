# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        move_ids = [vals.get("move_id") for vals in vals_list]
        moves = self.env["account.move"].browse(move_ids)
        # Allow to link journal entry to an asset
        allow_asset = all(move.move_type == "entry" for move in moves)
        return super(
            AccountMoveLine, self.with_context(allow_asset=allow_asset)
        ).create(vals_list)

    def write(self, vals):
        moves = self.mapped("move_id")
        ctx = self.env.context.copy()
        # Allow to link journal entry to an asset
        if all(move.move_type == "entry" for move in moves):
            ctx.update({"allow_asset_removal": True, "allow_asset": True})
        return super(AccountMoveLine, self.with_context(**ctx)).write(vals)
