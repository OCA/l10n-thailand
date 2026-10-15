# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

CURRENCY_RATE_TYPE = [
    ("mid_rate", "Mid Rate"),
    ("selling", "Selling Rate"),
    ("buying_sight", "Buying Sight Rate"),
    ("buying_transfer", "Buying Transfer Rate"),
]


class ResCurrency(models.Model):
    _inherit = "res.currency"

    bot_currency_name = fields.Char(
        string="BOT Currency",
        size=3,
        compute="_compute_bot_currency_name",
        readonly=False,
        store=True,
        required=True,
    )
    bot_currency_rate_type = fields.Selection(
        string="BOT Currency Rate Type",
        selection=CURRENCY_RATE_TYPE,
        default="mid_rate",
        required=True,
        index=True,
    )

    @api.depends("name")
    def _compute_bot_currency_name(self):
        for currency in self:
            currency.bot_currency_name = currency.name or "-"
