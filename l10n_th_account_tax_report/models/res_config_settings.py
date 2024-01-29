# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tax_report_format = fields.Selection(
        related="company_id.tax_report_format",
        readonly=False,
        required=True,
    )
    wht_report_format = fields.Selection(
        related="company_id.wht_report_format",
        readonly=False,
        required=True,
    )
