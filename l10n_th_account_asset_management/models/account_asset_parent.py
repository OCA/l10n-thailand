# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAssetParent(models.Model):
    _name = "account.asset.parent"
    _description = "Parent Asset"
    _order = "id desc"
    _check_company_auto = True
    _rec_names_search = ["code", "name"]

    asset_ids = fields.One2many(
        comodel_name="account.asset",
        inverse_name="parent_id",
        string="Assets",
        copy=False,
        check_company=True,
    )
    code = fields.Char(
        default="/",
        required=True,
        index=True,
        copy=False,
    )
    name = fields.Char(required=True, index=True)
    note = fields.Text()
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    @api.depends("name", "code")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.code and rec.code != "/":
                rec.display_name = f"[{rec.code}] {rec.name}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "/") == "/":
                code = (
                    self.env["ir.sequence"].next_by_code("account.asset.parent") or "/"
                )
                vals["code"] = code
        return super().create(vals_list)

    def action_view_assets(self):
        asset_ids = self.asset_ids
        action_dict = self.env["ir.actions.actions"]._for_xml_id(
            "account_asset_management.account_asset_action"
        )
        if len(asset_ids) == 1:
            res = self.env.ref(
                "account_asset_management.account_asset_view_form", False
            )
            action_dict["views"] = [(res and res.id or False, "form")]
            action_dict["res_id"] = asset_ids.id
        elif asset_ids:
            action_dict["domain"] = [("id", "in", asset_ids.ids)]
        else:
            action_dict = {"type": "ir.actions.act_window_close"}
        return action_dict
