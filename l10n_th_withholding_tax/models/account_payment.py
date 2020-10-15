# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Withholding Tax",
        help="Optional hidden field to keep wt_tax. Useful for case 1 tax only",
    )
