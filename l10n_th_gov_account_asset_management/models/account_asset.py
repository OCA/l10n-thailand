# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountAsset(models.Model):
    _inherit = "account.asset"

    remove_reason = fields.Char(string="Removed Reason")

    def _check_can_remove_multi(self):
        if any(asset.state not in ["open", "close"] for asset in self):
            raise UserError(_("You can remove running or close assets only!"))
        return True

    def action_remove_multi_assets(self):
        ctx = dict(self.env.context, active_ids=self.ids)
        action = {
            "view_mode": "form",
            "res_model": "account.asset.remove",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": ctx,
        }
        can_remove_multi = self._check_can_remove_multi()
        if can_remove_multi:
            low_value_lst = self.mapped("low_value")
            # Removing low value assets
            if all(low_value_lst):
                action["name"] = _("Remove Low Value Asset")
                action["view_id"] = self.env.ref(
                    "l10n_th_gov_account_asset_management.asset_low_value_remove_form"
                ).id
                return action
            # Removing normal assets
            elif all(not low_value for low_value in low_value_lst):
                action["name"] = _("Generate Asset Removal entries")
                action["view_id"] = self.env.ref(
                    "l10n_th_gov_account_asset_management.account_asset_remove_view_form"
                ).id
                return action
            # Cannot removing mixed assets
            raise UserError(
                _(
                    "You cannot remove low value assets and other assets at the same time!"
                )
            )
