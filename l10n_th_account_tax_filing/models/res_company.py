# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_from_id = fields.Many2one(
        comodel_name="account.account",
        string="Sales Tax Account",
    )
    account_to_id = fields.Many2one(
        comodel_name="account.account",
        string="Purchase Tax Account",
    )
    account_adjust_id = fields.Many2one(
        comodel_name="account.account",
        string="Adjust Tax Account",
    )
    tax_authority_id = fields.Many2one(
        comodel_name="res.partner",
    )
