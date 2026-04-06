# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    promptpay_ref1_field = fields.Char(
        string="PromptPay Ref1 Field",
        related="company_id.promptpay_ref1_field",
        readonly=False,
    )
    promptpay_ref2_field = fields.Char(
        string="PromptPay Ref2 Field",
        related="company_id.promptpay_ref2_field",
        readonly=False,
    )
