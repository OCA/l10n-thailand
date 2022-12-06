# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_report_format = fields.Selection(
        selection=[("std", "Standard"), ("rd", "Revenue Department")],
        default="std",
        required=True,
    )
    wht_report_format = fields.Selection(
        selection=[("std", "Standard"), ("rd", "Revenue Department")],
        default="std",
        required=True,
    )
