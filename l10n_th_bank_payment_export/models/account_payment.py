# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_export = fields.Boolean(
        string="Exported",
        copy=False,
        readonly=True,
        tracking=True,
    )
