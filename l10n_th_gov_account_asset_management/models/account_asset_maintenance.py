# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetMaintenance(models.Model):
    _name = "account.asset.maintenance"
    _description = "Asset Maintenance"
    _order = "date_maintenance desc"

    asset_id = fields.Many2one(
        comodel_name="account.asset",
        string="Asset",
        required=True,
        ondelete="cascade",
    )
    date_maintenance = fields.Date(
        string="Date",
        required=True,
    )
    ref = fields.Char(string="Reference")
    description = fields.Text()
