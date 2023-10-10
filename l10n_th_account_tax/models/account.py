# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    wht_account = fields.Boolean(
        string="WHT Account",
        default=False,
        help="If check, this account is for withholding tax",
    )
