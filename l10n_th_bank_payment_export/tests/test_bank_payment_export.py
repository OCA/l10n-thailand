# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError

from .common import CommonBankPaymentExport


class TestBankPaymentExport(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_create_payment_default_exported(self):
        """
        Check export status on payment when checked button 'Bank Payment Exported'
        on register payment wizard
        """
        # exported manual on wizard
        self.payment_exported_from_wizard = self.create_invoice_payment(
            amount=100,
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_manual_out,
            partner=self.partner_2,
            journal=self.journal_bank,
            is_export=True,
        )
        # multi invoices
        self.payment_multi_invoice_not_exported_from_wizard = (
            self.create_invoice_payment(
                amount=100,
                currency_id=self.main_currency_id,
                payment_method=self.payment_method_manual_out,
                partner=self.partner_2,
                journal=self.journal_bank,
                multi=True,
            )
        )
        self.payment_multi_invoice_exported_from_wizard = self.create_invoice_payment(
            amount=100,
            currency_id=self.main_currency_id,
            payment_method=self.payment_method_manual_out,
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
                self.payment3_out_method_check.id,
                self.payment4_out_currency.id,
                self.payment5_in.id,
                self.payment6_out_partner.id,
            ],
        }
        # Journal != Bank or Payment method != Manual
        with self.assertRaises(UserError):
            self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()
        # Delete payment that constraint
        del ctx["active_ids"][1]  # payment2_out_journal_cash
        del ctx["active_ids"][1]  # payment3_out_method_check
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
            self.payment1_out_journal_bank.export_status = "draft"

        # Payments state != posted can't export bank
        with self.assertRaises(UserError):
            self.payment1_out_journal_bank.action_draft()
            self.assertEqual(self.payment1_out_journal_bank.state, "draft")
            self.bank_payment_export_model.with_context(
                **ctx
            ).action_create_bank_payment_export()
            self.payment1_out_journal_bank.action_post()
            self.assertEqual(self.payment1_out_journal_bank.state, "posted")
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
            (
                sender_bank_code,
                sender_branch_code,
                sender_acc_number,
            ) = line._get_sender_information()
            # Default from recipient bank
            if line.payment_partner_id == self.partner_2:
                self.assertTrue(receiver_name)
                self.assertTrue(receiver_acc_number)

    def test_04_create_bank_payment_export_direct(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertNotEqual(bank_payment.name, "/")
        self.assertEqual(len(bank_payment.export_line_ids), 0)
        self.assertEqual(bank_payment.state, "draft")
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
        # bank payment export line must select recipient bank
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        for line in export_line:
            self.assertEqual(line.payment_id.export_status, "to_export")
            self.assertTrue(line.payment_id.payment_export_id)
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id

            # check bank account number can't use -
            keep_origin = line.payment_partner_bank_id.acc_number
            line.payment_partner_bank_id.acc_number = "Z000-Test"
            with self.assertRaises(UserError):
                bank_payment.action_confirm()
            # rollback data
            line.payment_partner_bank_id.acc_number = keep_origin

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
