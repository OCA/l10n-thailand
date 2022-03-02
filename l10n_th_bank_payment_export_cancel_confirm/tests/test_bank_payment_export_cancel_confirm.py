# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


class TestBankPaymentExportCancelConfirm(CommonBankPaymentExport):
    def setUp(self):
        super().setUp()
        self.cancel_confirm_model = self.env["cancel.confirm"]

    def test_01_cancel_confirm_line(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        self.assertEqual(bank_payment.state, "draft")
        self.assertEqual(len(bank_payment.export_line_ids.ids), 2)
        # Add recipient bank on line
        for line in bank_payment.export_line_ids:
            self.assertEqual(line.payment_id.export_status, "to_export")
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id
        bank_payment.action_confirm()
        self.assertEqual(bank_payment.state, "confirm")
        bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        # check export status on payment must be export
        for line in bank_payment.export_line_ids:
            self.assertEqual(line.payment_id.export_status, "exported")

        # Test reject 1 line, it should default wizard cancel confirm
        cancel_wizard_list = bank_payment.export_line_ids[0].action_reject()
        self.assertEqual(cancel_wizard_list["res_model"], "cancel.confirm")
        cancel_wizard = self.cancel_confirm_model.create(
            {
                "has_cancel_reason": cancel_wizard_list["context"][
                    "default_has_cancel_reason"
                ],
                "cancel_reason": "Text Cancel Reason",
            }
        )
        cancel_wizard.with_context(cancel_wizard_list["context"]).confirm_cancel()
        self.assertEqual(bank_payment.export_line_ids[0].state, "reject")
        # check export status on payment must be unlink with bank payment export
        self.assertEqual(
            bank_payment.export_line_ids[0].payment_id.export_status, "draft"
        )

        # Test cancel all line, it should auto cancel header too
        cancel_wizard_list2 = bank_payment.export_line_ids[1].action_reject()
        self.assertEqual(cancel_wizard_list2["res_model"], "cancel.confirm")
        cancel_wizard2 = self.cancel_confirm_model.create(
            {
                "has_cancel_reason": cancel_wizard_list2["context"][
                    "default_has_cancel_reason"
                ],
                "cancel_reason": "Text Cancel Reason",
            }
        )
        cancel_wizard2.with_context(cancel_wizard_list2["context"]).confirm_cancel()

        self.assertEqual(bank_payment.export_line_ids[1].state, "reject")
        self.assertEqual(bank_payment.state, "reject")

    def test_02_cancel_confirm_header(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        self.assertEqual(bank_payment.state, "draft")
        self.assertEqual(len(bank_payment.export_line_ids.ids), 2)
        # Add recipient bank on line
        for line in bank_payment.export_line_ids:
            self.assertEqual(line.payment_id.export_status, "to_export")
            if line.payment_partner_id == self.partner_2:
                # check default recipient bank
                self.assertTrue(line.payment_partner_bank_id)
            else:
                line.payment_partner_bank_id = self.partner1_bank_bnp.id
        bank_payment.action_confirm()
        self.assertEqual(bank_payment.state, "confirm")
        bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        # Test cancel header
        cancel_wizard_list = bank_payment.action_reject()
        self.assertEqual(cancel_wizard_list["res_model"], "cancel.confirm")
        cancel_wizard = self.cancel_confirm_model.create(
            {
                "has_cancel_reason": cancel_wizard_list["context"][
                    "default_has_cancel_reason"
                ],
                "cancel_reason": "Text Cancel Reason",
            }
        )
        cancel_wizard.with_context(cancel_wizard_list["context"]).confirm_cancel()
        self.assertEqual(bank_payment.state, "reject")
        for line in bank_payment.export_line_ids:
            self.assertEqual(line.state, "reject")
            # check export status on payment must be unlink with bank payment export
            self.assertEqual(line.payment_id.export_status, "draft")
