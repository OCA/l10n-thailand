# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.exceptions import ValidationError

_DATA_URI_PREFIX = "data:image/png;base64,"


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_promptpay_field_value(self, field_path):
        """Traverse dotted field path and return value as string.
        e.g. 'partner_id.name', 'name', 'partner_id.ref'
        """
        self.ensure_one()
        value = self
        for part in field_path.split("."):
            value = getattr(value, part, "") if value else ""
        return str(value) if value else ""

    def _get_promptpay_ref1(self):
        """Return Reference 1 for PromptPay QR. (Required)"""
        self.ensure_one()
        field_path = self.company_id.promptpay_ref1_field
        if not field_path:
            raise ValidationError(self.env._("PromptPay Ref1 Field is not set."))
        return self._get_promptpay_field_value(field_path)

    def _get_promptpay_ref2(self):
        """Return Reference 2 for PromptPay QR."""
        self.ensure_one()
        field_path = self.company_id.promptpay_ref2_field
        if field_path:
            return self._get_promptpay_field_value(field_path)
        return False

    def _get_value_promptpay_qr_code(self, bill_ref1, bill_ref2, qr_image):
        return {
            "invoice_id": self.id,
            "ref1": bill_ref1,
            "ref2": bill_ref2,
            "amount": self.amount_residual,
            "currency_id": self.currency_id.id,
            "proxy_type": self.partner_bank_id.proxy_type,
            "proxy_value": self.partner_bank_id.proxy_value,
            "qr_code_display": qr_image,
        }

    def generate_promptpay_qr(self):
        self.ensure_one()
        bill_ref1 = False
        bill_ref2 = False
        if self.partner_bank_id.proxy_type == "bill_payment":
            bill_ref1 = self._get_promptpay_ref1()
            bill_ref2 = self._get_promptpay_ref2()
        qr_data = self.with_context(
            bill_ref1=bill_ref1,
            bill_ref2=bill_ref2,
        )._generate_qr_code()
        qr_image = False
        if qr_data and qr_data.startswith(_DATA_URI_PREFIX):
            qr_image = qr_data[len(_DATA_URI_PREFIX) :]
        qr_value = self._get_value_promptpay_qr_code(bill_ref1, bill_ref2, qr_image)
        wizard = self.env["promptpay.qr.wizard"].create(qr_value)
        return {
            "type": "ir.actions.act_window",
            "name": "PromptPay QR Code",
            "res_model": "promptpay.qr.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }
