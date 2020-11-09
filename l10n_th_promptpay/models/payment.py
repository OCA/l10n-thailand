# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
# from odoo.addons.payment.models.payment_acquirer import ValidationError
# from odoo.tools.float_utils import float_compare
from promptpay import qrcode

import logging
import pprint


class l10n_th_promptpay(models.Model):
    _inherit = 'payment.acquirer'
    qr_code_promptpay =  fields.Boolean('Use PromptPay QR code')
    promptpay_id = fields.Char(string="PromptPay ID", help="13 digits for company's tax ID or 10 digits for mobile phone number")

    def promptpayPayload(self, data):
        return qrcode.generate_payload(self.promptpay_id,float(data))