# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_from_id = fields.Many2one(
        related="company_id.account_from_id",
        readonly=False,
        help="The starting account for the range of accounts used in tax filing.",
    )
    account_to_id = fields.Many2one(
        related="company_id.account_to_id",
        readonly=False,
        help="The ending account for the range of accounts used in tax filing.",
    )
    account_adjust_id = fields.Many2one(
        related="company_id.account_adjust_id",
        readonly=False,
        help="The account used for tax adjustments or corrections.",
    )
    tax_authority_id = fields.Many2one(
        related="company_id.tax_authority_id",
        readonly=False,
        help="The partner record representing the tax authority (e.g., Revenue Department).",
    )
