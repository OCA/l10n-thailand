# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPromptpay(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_th = cls.env.ref("base.th")
        cls.country_us = cls.env.ref("base.us")
        cls.currency_thb = cls.env.ref("base.THB")
        cls.currency_thb.active = True
        cls.currency_usd = cls.env.ref("base.USD")

        cls.qr_wizard = cls.env["promptpay.qr.wizard"]

        cls.company_data["company"].qr_code = True
        cls.company_data["company"].partner_id.update(
            {
                "country_id": cls.country_th.id,
                "city": "Thailand",
            }
        )

        # Thai partner - bank account country_code derives from partner country
        cls.partner_th = cls.env["res.partner"].create(
            {
                "name": "Test Partner TH",
                "country_id": cls.country_th.id,
                "ref": "CUST001",
            }
        )
        cls.partner_us = cls.env["res.partner"].create(
            {
                "name": "Test Partner US",
                "country_id": cls.country_us.id,
                "ref": "CUST002",
            }
        )

        cls.bank = cls.env["res.bank"].create(
            {"name": "Test Bank TH", "country": cls.country_th.id}
        )

    def _make_bank_account(
        self, proxy_type, proxy_value, partner=None, acc_number="1234567890"
    ):
        return self.env["res.partner.bank"].create(
            {
                "acc_number": acc_number,
                "allow_out_payment": True,
                "partner_id": (partner or self.company.partner_id).id,
                "bank_id": self.bank.id,
                "proxy_type": proxy_type,
                "proxy_value": proxy_value,
            }
        )

    def _make_invoice(self, partner_bank):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_th.id,
                "currency_id": self.currency_thb.id,
                "partner_bank_id": partner_bank.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test Service",
                            "quantity": 1,
                            "price_unit": 1500.0,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_01_check_validation(self):
        """All wrong-configuration cases must raise the appropriate error."""
        # Tax ID: less than 13 digits
        with self.assertRaises(ValidationError):
            self._make_bank_account(
                proxy_type="merchant_tax_id", proxy_value="123456789"
            )

        # Mobile: less than 10 digits
        with self.assertRaises(ValidationError):
            self._make_bank_account(proxy_type="mobile", proxy_value="081234")

        # Mobile: contains non-digit characters
        with self.assertRaises(ValidationError):
            self._make_bank_account(proxy_type="mobile", proxy_value="081-234-567")

        # Biller ID: 14 digits (too short)
        with self.assertRaises(ValidationError):
            self._make_bank_account(
                proxy_type="bill_payment", proxy_value="01234567890123"
            )

        # Biller ID: 16 digits (too long)
        with self.assertRaises(ValidationError):
            self._make_bank_account(
                proxy_type="bill_payment", proxy_value="0123456789012345"
            )

        # Non-THB currency:
        # _get_error_messages_for_qr must return an error containing "THB"
        bank = self._make_bank_account(proxy_type="mobile", proxy_value="0812345678")
        error = bank._get_error_messages_for_qr(
            "emv_qr", self.partner_th, self.currency_usd
        )
        self.assertIsNotNone(error)

        # THB currency: _get_error_messages_for_qr must return None
        error = bank._get_error_messages_for_qr(
            "emv_qr", self.partner_th, self.currency_thb
        )
        self.assertIsNone(error)

        # Change partner country is not Thai,
        # _get_error_messages_for_qr must return Error
        self.assertEqual(bank.partner_id.country_id, self.country_th)
        self.assertEqual(bank.country_code, self.country_th.code)
        bank.partner_id.write({"country_id": self.country_us})
        self.assertEqual(bank.country_code, self.country_us.code)
        error = bank._get_error_messages_for_qr(
            "emv_qr", self.partner_th, self.currency_thb
        )
        self.assertIsNotNone(error)

        # Check qr code error (Not Bank Thai), It should return None
        error = bank._check_for_qr_code_errors(
            "emv_qr", 1000.0, self.currency_thb, self.partner_th, "", ""
        )
        self.assertIsNone(error)

    def test_02_no_proxy_type(self):
        # No proxy_type: _check_for_qr_code_errors must return an error
        bank_none = self._make_bank_account(proxy_type="none", proxy_value=False)
        error = bank_none._check_for_qr_code_errors(
            "emv_qr", 1000.0, self.currency_thb, self.partner_th, "", ""
        )
        self.assertIsNotNone(error)

    def test_03_generate_qr_credit_transfer_wizard(self):
        """generate_promptpay_qr on invoice returns a wizard with QR data."""
        bank = self._make_bank_account(proxy_type="mobile", proxy_value="0812345678")
        self.assertTrue(bank.display_qr_setting)
        invoice = self._make_invoice(bank)
        self.assertTrue(invoice.display_qr_code)
        action = invoice.generate_promptpay_qr()
        self.assertEqual(action["res_model"], "promptpay.qr.wizard")
        wizard = self.qr_wizard.browse(action["res_id"])
        self.assertEqual(wizard.invoice_id, invoice)
        self.assertEqual(wizard.proxy_type, "mobile")
        self.assertEqual(wizard.proxy_value, "0812345678")
        self.assertEqual(wizard.amount, invoice.amount_residual)
        # No ref fields configured for credit transfer
        self.assertFalse(wizard.ref1)
        self.assertFalse(wizard.ref2)

        # Check value credir transfer
        tag_id, data = bank._get_merchant_account_info()

        self.assertIn("A000000677010111", data)
        self.assertIn("66812345678", data)  # replace 0 to 66
        self.assertEqual(tag_id, 29)

    def test_04_generate_qr_bill_payment_wizard(self):
        """Bill Payment QR: tag_id=30, AID=A000000677010112, Biller ID included."""
        self.company.promptpay_ref1_field = "partner_id.ref"
        self.company.promptpay_ref2_field = "name"

        bank = self._make_bank_account(
            proxy_type="bill_payment", proxy_value="012345678901234"
        )
        invoice = self._make_invoice(bank)

        action = invoice.generate_promptpay_qr()
        self.assertEqual(action["res_model"], "promptpay.qr.wizard")
        wizard = self.qr_wizard.browse(action["res_id"])

        self.assertEqual(wizard.invoice_id, invoice)
        self.assertEqual(wizard.proxy_type, "bill_payment")
        self.assertEqual(wizard.proxy_value, "012345678901234")
        self.assertEqual(wizard.ref1, invoice.partner_id.ref)
        self.assertEqual(wizard.ref2, invoice.name)
        self.assertEqual(wizard.amount, invoice.amount_residual)
        self.assertEqual(wizard.currency_id, self.currency_thb)

        # Check value bill payment
        bill_ref1 = invoice._get_promptpay_ref1()
        bill_ref2 = invoice._get_promptpay_ref2()
        tag_id, data = bank.with_context(
            bill_ref1=bill_ref1,
            bill_ref2=bill_ref2,
        )._get_merchant_account_info()

        self.assertIn("A000000677010112", data)
        self.assertIn("012345678901234", data)
        self.assertIn("CUST001", data)
        self.assertIn(invoice.name, data)
        self.assertEqual(tag_id, 30)

    def test_05_bill_payment_without_ref(self):
        self.company.promptpay_ref1_field = ""
        self.company.promptpay_ref2_field = ""

        bank = self._make_bank_account(
            proxy_type="bill_payment", proxy_value="012345678901234"
        )
        invoice = self._make_invoice(bank)

        # Ref1 required
        with self.assertRaisesRegex(
            ValidationError,
            "PromptPay Ref1 Field is not set.",
        ):
            action = invoice.generate_promptpay_qr()

        # Add ref1
        self.company.promptpay_ref1_field = "partner_id.ref"

        action = invoice.generate_promptpay_qr()
        self.assertEqual(action["res_model"], "promptpay.qr.wizard")
        wizard = self.qr_wizard.browse(action["res_id"])

        self.assertEqual(wizard.invoice_id, invoice)
        self.assertEqual(wizard.proxy_type, "bill_payment")
        self.assertEqual(wizard.proxy_value, "012345678901234")
        self.assertEqual(wizard.ref1, invoice.partner_id.ref)
        self.assertEqual(wizard.ref2, False)
        self.assertEqual(wizard.amount, invoice.amount_residual)
        self.assertEqual(wizard.currency_id, self.currency_thb)
