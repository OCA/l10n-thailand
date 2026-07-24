# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PromptpayQrWizard(models.TransientModel):
    _name = "promptpay.qr.wizard"
    _description = "PromptPay QR Code Wizard"

    invoice_id = fields.Many2one(
        comodel_name="account.move",
        required=True,
        readonly=True,
    )
    ref1 = fields.Char(
        string="Reference 1",
        readonly=True,
    )
    ref2 = fields.Char(
        string="Reference 2",
        readonly=True,
    )
    amount = fields.Monetary(
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        readonly=True,
    )
    proxy_type = fields.Selection(
        selection=[
            ("ewallet_id", "Ewallet ID"),
            ("merchant_tax_id", "Merchant Tax ID"),
            ("mobile", "Mobile Number"),
            ("bill_payment", "Bill Payment"),
        ],
    )
    proxy_value = fields.Char(
        readonly=True,
    )
    qr_code_display = fields.Binary(
        string="QR Code",
        readonly=True,
    )
