# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetSubState(models.Model):
    _name = "account.asset.sub.state"
    _description = "Asset Sub Status"
    _order = "sequence"
    _check_company_auto = True

    sequence = fields.Integer(
        default=10,
        help="Used to order Asset Sub Status",
    )
    name = fields.Char(
        required=True,
        index=True,
    )
    note = fields.Text()
    draft = fields.Boolean(
        index=True,
        help="Show this asset sub-status on the draft asset",
    )
    open = fields.Boolean(
        string="Running",
        index=True,
        help="Show this asset sub-status on the running asset",
    )
    close = fields.Boolean(
        index=True,
        help="Show this asset sub-status on the close asset",
    )
    removed = fields.Boolean(
        index=True,
        help="Show this asset sub-status on the removed asset",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
