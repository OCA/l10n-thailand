# Copyright 2020 Poonlap V.
# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from promptpay import qrcode

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    qr_code_promptpay = fields.Boolean(string="Use PromptPay QR code")
    promptpay_id = fields.Char(
        string="PromptPay ID",
        help="13 digits for company's tax ID or 10 digits for mobile phone number",
    )

    def promptpayPayload(self, data):
        return qrcode.generate_payload(self.promptpay_id, float(data))
