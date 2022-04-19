# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    bbl_config_ewht = fields.Boolean(
        related="company_id.bbl_config_ewht",
        string="Payment Export BBL with eWHT",
        readonly=False
    )