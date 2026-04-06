# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    promptpay_ref1_field = fields.Char(
        string="PromptPay Ref1 Field",
        default="partner_id.ref",
        help="Field path from Invoice used as Reference 1 in PromptPay QR code. "
        "Supports dotted path e.g. 'name', 'partner_id.name', 'partner_id.ref'.",
    )
    promptpay_ref2_field = fields.Char(
        string="PromptPay Ref2 Field",
        help="Field path from Invoice used as Reference 2 in PromptPay QR code. "
        "Supports dotted path e.g. 'Payment Reference'.",
    )
