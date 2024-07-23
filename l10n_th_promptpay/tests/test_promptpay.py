# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestPromptpay(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wire_transfer = cls.env.ref("payment.payment_provider_transfer")

    def test_01_generate_promptpay(self):
        """verify that amount_to_text converted text to thai language"""
        self.wire_transfer.qr_code_promptpay = True
        self.wire_transfer.promptpay_id = "1234567890123"
        result = self.wire_transfer.promptpayPayload(1000.25)
        # In format promptpay, it should have promptpay_id and amount in result
        self.assertIn("1234567890123", result)
        self.assertIn("1000.25", result)
