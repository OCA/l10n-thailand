# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError

from .common import CommonBankPaymentExport


class TestBankPaymentExport(CommonBankPaymentExport):
    def setUp(self):
        super().setUp()

    def test_01_create_bank_payment_export_from_payment(self):
        """ Create bank payment export from vendor payment"""
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
                ctx
            ).action_create_bank_payment_export()
        # Delete payment that constraint
        del ctx["active_ids"][1]  # payment2_out_journal_cash
        del ctx["active_ids"][1]  # payment3_out_method_check
        del ctx["active_ids"][2]  # payment5_in
        # Payment currency following main currency only
        with self.assertRaises(UserError):
            self.bank_payment_export_model.with_context(
                ctx
            ).action_create_bank_payment_export()
        del ctx["active_ids"][1]  # payment4_out_currency

        # Payments have been already exported
        with self.assertRaises(UserError):
            self.assertFalse(self.payment1_out_journal_bank.is_export)
            self.payment1_out_journal_bank.is_export = True
            self.bank_payment_export_model.with_context(
                ctx
            ).action_create_bank_payment_export()
            self.payment1_out_journal_bank.is_export = False

        # Payments state != posted can't export bank
        with self.assertRaises(UserError):
            self.payment1_out_journal_bank.action_draft()
            self.assertEqual(self.payment1_out_journal_bank.state, "draft")
            self.bank_payment_export_model.with_context(
                ctx
            ).action_create_bank_payment_export()
            self.payment1_out_journal_bank.action_post()
            self.assertEqual(self.payment1_out_journal_bank.state, "posted")
        action = self.bank_payment_export_model.with_context(
            ctx
        ).action_create_bank_payment_export()
        self.assertEqual(len(action["context"]["default_export_line_ids"]), 2)

    def test_02_common_function(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids.ids), 2)
        report_name = bank_payment._get_report_base_filename()
        self.assertEqual(report_name, bank_payment.name)
        for line in bank_payment.export_line_ids:
            (
                receiver_name,
                receiver_bank_code,
                receiver_branch_code,
                receiver_acc_number,
            ) = line._get_receiver_information()
            (
                sender_bank_code,
                sender_branch_code,
                sender_acc_number,
            ) = line._get_sender_information()
            # Default from recipient bank
            if line.payment_partner_id == self.partner_2:
                self.assertTrue(receiver_name)
                self.assertTrue(receiver_acc_number)

    def test_03_create_bank_payment_export_direct(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertNotEqual(bank_payment.name, "/")
        self.assertEqual(len(bank_payment.export_line_ids), 0)
        self.assertEqual(bank_payment.state, "draft")
        # Test unlink document state draft
        bank_payment.unlink()
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        # export line is null
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        bank_payment.action_get_all_payments()
        # payment1_out_journal_bank and payment6_out_partner
        self.assertEqual(len(bank_payment.export_line_ids), 2)
        export_line = bank_payment.export_line_ids
        # payment exported can't confirm
        with self.assertRaises(UserError):
            self.assertFalse(self.payment1_out_journal_bank.is_export)
            self.payment1_out_journal_bank.is_export = True
            bank_payment.action_confirm()
            self.payment1_out_journal_bank.is_export = False
        # bank payment export line must select recipient bank
        with self.assertRaises(UserError):
            bank_payment.action_confirm()
        for line in export_line:
            self.assertFalse(line.payment_id.is_export)
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id
        bank_payment.action_confirm()
        self.assertEqual(bank_payment.state, "confirm")
        for line in export_line:
            self.assertTrue(line.payment_id.is_export)
        # Test state reset to draft, all payment must export = False
        bank_payment.action_draft()
        for line in export_line:
            self.assertFalse(line.payment_id.is_export)
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
        # Cancel some payment
        export_line[0].action_cancel()
        self.assertEqual(export_line[0].state, "cancel")
        self.assertNotEqual(export_line[0].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 2)
        # Cancel all payment, state bank export must cancel too.
        export_line[1].action_cancel()
        self.assertEqual(export_line[1].state, "cancel")
        self.assertEqual(export_line[1].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 1)

        # Check unlink document not state draft
        with self.assertRaises(UserError):
            bank_payment.unlink()
