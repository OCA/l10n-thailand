# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    api_client_id = fields.Char()
    route_path = fields.Char(
        default="https://apigw1.bot.or.th/bot/public/financial-institutions-holidays/",
    )
