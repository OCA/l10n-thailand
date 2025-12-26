# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    api_client_id = fields.Char(
        related="company_id.api_client_id",
        readonly=False,
    )
    route_path = fields.Char(
        string="Route Path",
        related="company_id.route_path",
        readonly=False,
    )
