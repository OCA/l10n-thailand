# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_filing_id = fields.Many2one(
        comodel_name="account.tax.filing",
        copy=False,
        readonly=True,
        index=True,
    )
