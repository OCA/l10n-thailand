# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_ac_payee = fields.Boolean(
        string="A/C. Payee Only",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    lang_amount_check = fields.Selection(
        selection=[("en_US", "English"), ("th_TH", "Thai")],
        string="Language Amount Word",
        default=lambda self: self.env.user.lang,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
