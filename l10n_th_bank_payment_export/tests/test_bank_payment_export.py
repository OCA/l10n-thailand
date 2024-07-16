# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form

from .common import CommonBankPaymentExport


class TestBankPaymentExport(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # setup template
        field_effective_date = cls.field_model.search(
            [("name", "=", "effective_date"), ("model", "=", "bank.payment.export")]
        )
        cls.template_test_bank = cls.create_bank_payment_template(
            cls,
            "TEST",
            [
                {
                    "field_id": field_effective_date.id,
                    "value": "9999-01-01",
                }
            ],
        )

    def test_01_create_payment_default_exported(self):
        """
        Check export status on payment when checked button 'Bank Payment Exported'
        on register payment wizard
        """
        # exported manual on wizard
        self.payment_exported_from_wizard = self.create_invoice_payment(
            amount=100,
            currency_id=self.main_currency_id,
            payment_method=self.journal_bank_manual_out,
            partner=self.partner_2,
            journal=self.journal_bank,
            is_export=True,
        )
        # multi invoices
        self.payment_multi_invoice_not_exported_from_wizard = (
            self.create_invoice_payment(
                amount=100,
                currency_id=self.main_currency_id,
                payment_method=self.journal_bank_manual_out,
                partner=self.partner_2,
                journal=self.journal_bank,
                multi=True,
            )
        )
        self.payment_multi_invoice_exported_from_wizard = self.create_invoice_payment(
            amount=100,
            currency_id=self.main_currency_id,
            payment_method=self.journal_bank_manual_out,
            partner=self.partner_2,
            journal=self.journal_bank,
            is_export=True,
            multi=True,
        )
        self.assertEqual(self.payment_exported_from_wizard.export_status, "exported")
        for payment in self.payment_multi_invoice_exported_from_wizard:
            self.assertEqual(payment.export_status, "exported")
            self.assertFalse(payment.payment_export_id)
        for payment in self.payment_multi_invoice_not_exported_from_wizard:
            self.assertEqual(payment.export_status, "draft")
            self.assertFalse(payment.payment_export_id)

    def test_02_create_bank_payment_export_from_payment(self):
        """Create bank payment export from vendor payment"""
        ctx = {
            "active_model": "account.payment",
            "active_ids": [
                self.payment1_out_journal_bank.id,
                self.payment2_out_journal_cash.id,
                # self.payment3_out_method_check.id,
                self.payment4_out_currency.id,
                self.payment5_in.id,
                self.payment6_out_partner.id,
            ],
        }
        # Not active_ids, it should return False
        action = self.bank_payment_export_model.with_context(
            active_model="account.payment"
        ).action_create_bank_payment_export()
        self.assertFalse(action)
        # Journal != Bank or Payment method != Manual
        with self.assertRaises(UserError):
            self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()
        # Delete payment that constraint
        del ctx["active_ids"][1]  # payment2_out_journal_cash
        # del ctx["active_ids"][1]  # payment3_out_method_check
        del ctx["active_ids"][2]  # payment5_in
        # Payment currency following main currency only
        with self.assertRaises(UserError):
            self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()
        del ctx["active_ids"][1]  # payment4_out_currency

        # Payments have been already exported
        with self.assertRaises(UserError):
            self.assertEqual(self.payment1_out_journal_bank.export_status, "draft")
            # Test with change state != draft
            self.payment1_out_journal_bank.export_status = "to_export"
            self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()

        # Payments state != posted can't export bank
        with self.assertRaises(UserError):
            self.payment1_out_journal_bank.action_draft()
            self.assertEqual(self.payment1_out_journal_bank.state, "draft")
            self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()
        # Test payment with not same template
        with self.assertRaises(UserError):
            self.payment1_out_journal_bank.bank_payment_template_id = (
                self.template_test_bank.id
            )
            action = self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()

        action = self.bank_payment_export_model.with_context(
            **ctx
        ).action_create_bank_payment_export()
        self.assertEqual(len(action["context"]["default_export_line_ids"]), 2)

    def test_03_common_function(self):
        """Check other module can call common function and get this result"""
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertFalse(bank_payment.export_line_ids)
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids.ids), 2)
        self.assertFalse(bank_payment.is_required_effective_date)
        # Test function for generate text file
        amount_test = bank_payment._get_amount_no_decimal(100.0)
        self.assertEqual(amount_test, 100.0)
        text_file = bank_payment._generate_bank_payment_text()
        self.assertEqual(
            "Demo Text File. You can inherit function _generate_bank_payment_text() "
            "for customize your format.",
            text_file,
        )
        # Test bank difference bank payment
        with self.assertRaises(UserError):
            bank_payment.export_line_ids[
                0
            ].payment_journal_id.bank_id = self.bank_ing.id
            bank_payment.bank = "TEST"
        bank_payment.check_bank_payment()
        with self.assertRaises(UserError):
            bank_payment.effective_date = "2020-01-01"  # check back date effective date

        report_name = bank_payment._get_report_base_filename()
        self.assertEqual(report_name, bank_payment.name)
        for i, line in enumerate(bank_payment.export_line_ids):
            # Test Bank of Customer has account number more than 11 digits
            if i == 0:
                # BAABTHBK 12 digits -> 11 digits (2 - 12)
                line.payment_partner_bank_id.bank_id.bic = "BAABTHBK"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                (
                    receiver_name,
                    receiver_bank_code,
                    receiver_branch_code,
                    receiver_acc_number,
                ) = line._get_receiver_information()
                self.assertEqual(len(receiver_acc_number), 11)
                self.assertEqual(receiver_acc_number, "23456789012")
                # TFPCTHB1 14 digits -> 11 digits (5 - 14 and add 0 at first digit)
                line.payment_partner_bank_id.bank_id.bic = "TFPCTHB1"
                line.payment_partner_bank_id.acc_number = "12345678901234"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 14)
                (
                    receiver_name,
                    receiver_bank_code,
                    receiver_branch_code,
                    receiver_acc_number,
                ) = line._get_receiver_information()
                self.assertEqual(len(receiver_acc_number), 11)
                self.assertEqual(receiver_acc_number, "05678901234")
                # TIBTTHBK 12 digits -> 11 digits (3 - 12 and add 0 at first digit)
                line.payment_partner_bank_id.bank_id.bic = "TIBTTHBK"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                (
                    receiver_name,
                    receiver_bank_code,
                    receiver_branch_code,
                    receiver_acc_number,
                ) = line._get_receiver_information()
                self.assertEqual(len(receiver_acc_number), 11)
                self.assertEqual(receiver_acc_number, "03456789012")
                # GSBATHBK 12 digits -> 11 digits (2 - 12)
                line.payment_partner_bank_id.bank_id.bic = "GSBATHBK"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                (
                    receiver_name,
                    receiver_bank_code,
                    receiver_branch_code,
                    receiver_acc_number,
                ) = line._get_receiver_information()
                self.assertEqual(len(receiver_acc_number), 11)
                self.assertEqual(receiver_acc_number, "23456789012")
                # Test other bank, it will nothing to do
                line.payment_partner_bank_id.bank_id.bic = "TESTNOBANKCODE"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                (
                    receiver_name,
                    receiver_bank_code,
                    receiver_branch_code,
                    receiver_acc_number,
                ) = line._get_receiver_information()
                self.assertEqual(len(receiver_acc_number), 12)
                self.assertEqual(receiver_acc_number, "123456789012")
            (
                sender_bank_code,
                sender_branch_code,
                sender_acc_number,
            ) = line._get_sender_information()
            # Default from recipient bank
            if line.payment_partner_id == self.partner_2:
                self.assertTrue(receiver_name)
                self.assertTrue(receiver_acc_number)
            # Test decimal
            self.assertEqual(line._get_amount_no_decimal(100.12345), 100.12345)
            # Test no account number
            test_no_acc = self.partner1_bank_bnp.copy()
            test_no_acc.acc_number = ""
            result = line._get_acc_number_digit(test_no_acc)
            self.assertEqual(result, "**receiver account number is null**")
            # Test account number < 11, it add until 11 digits
            test_no_acc.acc_number = "123"
            result = line._get_acc_number_digit(test_no_acc)
            self.assertEqual(result, "00000000123")

        # Test register payment with not group payment
        invoice = self.create_invoice(
            10.0, "in_invoice", self.main_currency_id, self.partner_2
        )
        ctx = {"active_model": "account.move", "active_ids": invoice.ids}
        register_payments = self.register_payments_model.with_context(**ctx).create(
            {
                "journal_id": self.journal_bank.id,
                "payment_method_line_id": self.journal_bank_manual_out.id,
                "amount": 10.0,
                "partner_bank_id": invoice.partner_bank_id.id,
                "payment_date": fields.Date.today(),
                "is_export": True,
                "group_payment": False,
            }
        )
        payment_list = register_payments.action_create_payments()
        payment = self.env["account.payment"].search(
            [("id", "=", payment_list["res_id"])]
        )
        self.assertEqual(payment.export_status, "exported")

        # Check function create payment vals must have 'export_status'
        batches = register_payments._get_batches()
        payment_vals = register_payments._create_payment_vals_from_batch(batches[0])
        self.assertTrue(payment_vals["export_status"])

    def test_04_create_bank_payment_export_direct(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertNotEqual(bank_payment.name, "/")
        self.assertEqual(len(bank_payment.export_line_ids), 0)
        self.assertEqual(bank_payment.state, "draft")
        self.assertFalse(bank_payment.bank)
        with Form(bank_payment) as pe:
            pe.template_id = self.template_test_bank
        bank_payment = pe.save()
        self.assertEqual(bank_payment.bank, "TEST")
        # Test unlink document state draft
        bank_payment.unlink()

        # Test cancel document (Account Manager)
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertEqual(bank_payment.state, "draft")
        bank_payment.action_cancel()
        self.assertEqual(bank_payment.state, "cancel")

        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        # export line is null
        with self.assertRaises(UserError):
            bank_payment.action_confirm()

        bank_payment.action_get_all_payments()
        # payment1_out_journal_bank and payment6_out_partner
        self.assertEqual(len(bank_payment.export_line_ids), 2)

        export_line = bank_payment.export_line_ids
        for line in export_line:
            self.assertEqual(line.payment_id.export_status, "to_export")
            self.assertTrue(line.payment_id.payment_export_id)
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id

        bank_payment.action_confirm()
        self.assertEqual(bank_payment.state, "confirm")
        bank_payment.action_draft()  # check state draft
        self.assertEqual(bank_payment.state, "draft")
        bank_payment.action_confirm()

        # Export Excel
        xlsx_data = self.action_bank_export_excel(bank_payment)
        self.assertEqual(xlsx_data[1], "xlsx")
        # Export Text File
        text_list = bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = bank_payment._export_bank_payment_text_file()
        self.assertEqual(
            text_word,
            "Demo Text File. You can inherit function "
            "_generate_bank_payment_text() for customize your format.",
        )
        # Reject some payment (bank reject)
        export_line[0].action_reject()
        self.assertEqual(export_line[0].state, "reject")
        self.assertNotEqual(export_line[0].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 2)
        # Reject all payment, state bank export must reject too.
        export_line[1].action_reject()
        self.assertEqual(export_line[1].state, "reject")
        self.assertEqual(export_line[1].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 1)

        # Check unlink document not state draft
        with self.assertRaises(UserError):
            bank_payment.unlink()
