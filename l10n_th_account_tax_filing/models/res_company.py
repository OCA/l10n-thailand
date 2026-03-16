# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_from_id = fields.Many2one(
        string="Sales Tax Account",
        comodel_name="account.account",
        domain=lambda self: [
            ("user_type_id.type", "not in", ["payable", "receivable", "liquidity"]),
            ("user_type_id.internal_group", "=", "liability"),
        ],
    )
    account_to_id = fields.Many2one(
        string="Purchase Tax Account",
        comodel_name="account.account",
        domain=lambda self: [
            ("user_type_id.type", "not in", ["payable", "receivable", "liquidity"]),
            ("user_type_id.internal_group", "=", "asset"),
        ],
    )
    account_adjust_id = fields.Many2one(
        string="Adjust Tax Account",
        comodel_name="account.account",
    )
    tax_authority_id = fields.Many2one(
        comodel_name="res.partner",
    )
