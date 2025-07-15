# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

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

        data_dict = [
            {
                "field_id": field_effective_date.id,
                "value": "9999-01-01",
            }
        ]

        cls.template_test_bank = cls.create_bank_payment_template(
            cls,
            "TEST",
            data_dict,
        )
        cls.bank_export_format = cls.bank_export_format_model.create(
            {
                "name": "Test Bank",
                "bank": "TEST",
                "export_format_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "lenght": 10,
                            "name": "Test Line1",
                            "value_type": "fixed",
                            "value": "9999999999",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 11,
                            "lenght": 4,
                            "name": "Test Line2",
                            "value_type": "fixed",
                            "value": "TEST",
                        },
                    ),
                ],
            }
        )

    def test_01_bank_export_format(self):
        # Lenght start with 1
        self.assertEqual(self.bank_export_format.export_format_ids[0].lenght_from, 1)
        self.assertEqual(self.bank_export_format.export_format_ids[0].lenght_to, 10)
        self.assertEqual(len(self.bank_export_format.export_format_ids), 2)

        # It should use same as lenght, when create line name and value duplicate
        self.bank_export_format.write(
            {
                "export_format_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 12,
                            "lenght": 4,
                            "name": "Test Line2",
                            "value_type": "fixed",
                            "value": "TEST",
                        },
                    )
                ]
            }
        )
        self.assertEqual(len(self.bank_export_format.export_format_ids), 3)
        self.assertEqual(self.bank_export_format.export_format_ids[1].lenght_from, 11)
        self.assertEqual(self.bank_export_format.export_format_ids[2].lenght_from, 11)

        # It should start new lenght, when end line
        self.bank_export_format.write(
            {
                "export_format_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 13,
                            "lenght": 4,
                            "name": "Test End Line",
                            "value_type": "fixed",
                            "value": "TEST",
                            "end_line": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 14,
                            "lenght": 4,
                            "name": "Test After End Line",
                            "value_type": "fixed",
                            "value": "TEST",
                        },
                    ),
                ]
            }
        )
        self.assertEqual(len(self.bank_export_format.export_format_ids), 5)
        self.assertEqual(self.bank_export_format.export_format_ids[-1].lenght_from, 1)

        # It should error, when value is longer than lenght
        with self.assertRaises(UserError):
            self.bank_export_format.export_format_ids.write(
                {
                    "sequence": 12,
                    "lenght": 5,
                    "name": "Test Line3",
                    "value_type": "fixed",
                    "value": "123456",
                }
            )

    def test_02_create_payment_default_exported(self):
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

    def test_03_create_bank_payment_export_from_payment(self):
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

    def test_04_common_function(self):
        """Check other module can call common function and get this result"""
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertFalse(bank_payment.export_line_ids)
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids.ids), 2)
        self.assertFalse(bank_payment.is_required_effective_date)
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
                # No account number, return "**receiver account number is null**"
                line.payment_partner_bank_id.bank_id.bic = "KRTHTHBK"
                line.payment_partner_bank_id.acc_number = False
                self.assertFalse(line.payment_partner_bank_id.acc_number)
                result = line._get_acc_number_digit(line.payment_partner_bank_id)
                self.assertEqual(result, "**receiver account number is null**")

                # KRTHTHBK 11 digits, nothing to do.
                line.payment_partner_bank_id.bank_id.bic = "KRTHTHBK"
                line.payment_partner_bank_id.acc_number = "12345678901"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 11)
                result = line._get_acc_number_digit(line.payment_partner_bank_id)
                self.assertEqual(len(result), 11)

                # BAABTHBK 12 digits -> 11 digits (2 - 12)
                line.payment_partner_bank_id.bank_id.bic = "BAABTHBK"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                result = line._get_acc_number_digit(line.payment_partner_bank_id)
                self.assertEqual(len(result), 11)

                # TFPCTHB1 14 digits -> 11 digits (5 - 14 and add 0 at first digit)
                line.payment_partner_bank_id.bank_id.bic = "TFPCTHB1"
                line.payment_partner_bank_id.acc_number = "12345678901234"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 14)
                result = line._get_acc_number_digit(line.payment_partner_bank_id)
                self.assertEqual(len(result), 11)

                # TIBTTHBK 12 digits -> 11 digits (3 - 12 and add 0 at first digit)
                line.payment_partner_bank_id.bank_id.bic = "TIBTTHBK"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                result = line._get_acc_number_digit(line.payment_partner_bank_id)
                self.assertEqual(len(result), 11)

                # GSBATHBK 12 digits -> 11 digits (2 - 12)
                line.payment_partner_bank_id.bank_id.bic = "GSBATHBK"
                line.payment_partner_bank_id.acc_number = "123456789012"
                self.assertEqual(len(line.payment_partner_bank_id.acc_number), 12)
                result = line._get_acc_number_digit(line.payment_partner_bank_id)
                self.assertEqual(len(result), 11)

                # Test sanitize_account_number
                result = line.sanitize_account_number("1-2345-6789")
                self.assertEqual(result, "123456789")

        # Test register payment with not group payment
        invoice = self.create_invoice(
            10.0, "in_invoice", self.main_currency_id, self.partner_2
        )
        payment_list = self._get_payment_list(
            invoice,
            10.0,
            self.journal_bank_manual_out,
            self.partner_2,
            self.journal_bank,
            is_export=True,
            group_payment=False,
        )
        payment = self.env["account.payment"].search(
            [("id", "=", payment_list["res_id"])]
        )
        self.assertEqual(payment.export_status, "exported")

        # Test get address with lenght max 99
        address = bank_payment._get_address(payment.partner_id, 99)
        self.assertIn(payment.partner_id.street, address)

    def test_05_create_bank_payment_export_direct(self):
        # 1. Test delete document with state draft
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertNotEqual(bank_payment.name, "/")
        self.assertEqual(len(bank_payment.export_line_ids), 0)
        self.assertEqual(bank_payment.state, "draft")
        self.assertFalse(bank_payment.bank)
        with Form(bank_payment) as pe:
            pe.template_id = self.template_test_bank
            pe.bank_export_format_id = self.bank_export_format
        bank_payment = pe.save()
        self.assertEqual(bank_payment.bank, "TEST")
        bank_payment.unlink()

        # 2. Test cancel document (Account Manager)
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertEqual(bank_payment.state, "draft")
        bank_payment.action_cancel()
        self.assertEqual(bank_payment.state, "cancel")

        # 3. Check line is not empty
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        with self.assertRaises(UserError):
            bank_payment.action_confirm()

        # 4. Get all payment and check default payment
        #     - payment1_out_journal_bank
        #     - payment6_out_partner
        bank_payment.action_get_all_payments()
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

        # 5. Test reject some payment line (Assume bank rejected)
        export_line[0].action_reject()
        self.assertEqual(export_line[0].state, "reject")
        self.assertNotEqual(export_line[0].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 2)

        # 6. Test reject all payment line, state bank export must reject too.
        export_line[1].action_reject()
        self.assertEqual(export_line[1].state, "reject")
        self.assertEqual(export_line[1].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 1)

        # 7. Test delete document with state is not draft
        with self.assertRaises(UserError):
            bank_payment.unlink()

    def test_06_export_text_file(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 2)

        # Test Export Text File (No bank)
        text_list = bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = bank_payment._export_bank_payment_text_file()
        self.assertEqual(
            text_word,
            "Demo Text File. You must config `Bank Export Format` First.",
        )

        # It should error, whengenerate text file without export format
        self.assertFalse(bank_payment.bank_export_format_id)
        with self.assertRaises(UserError):
            bank_payment._generate_bank_payment_text()

        # Add new format
        self.bank_export_format.write(
            {
                "export_format_ids": [
                    (
                        0,
                        0,
                        {
                            # Display Type
                            "sequence": 12,
                            "lenght": 4,
                            "display_type": "line_section",
                            "name": "Test End Line",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            # Match Group
                            "sequence": 13,
                            "lenght": 11,
                            "name": "Test match group",
                            "match_group": "A01",
                            "value_type": "fixed",
                            "value": "match group",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            # Need Loop
                            "sequence": 14,
                            "lenght": 9,
                            "name": "Test loop",
                            "match_group": "A01",
                            "value_type": "fixed",
                            "value": "need loop",
                            "need_loop": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            # Condition Line
                            "sequence": 15,
                            "lenght": 9,
                            "name": "Test Condition",
                            "value_type": "fixed",
                            "value": "condition",
                            "condition_line": "[(1, '=', 1)]",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            # Need Loop, Sub Loop
                            "sequence": 16,
                            "lenght": 9,
                            "name": "Test sub loop",
                            "value_type": "fixed",
                            "value": "need loop",
                            "need_loop": True,
                            "sub_loop": True,
                            "sub_value_loop": "line",
                            "match_group": "A02",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            # End Line
                            "sequence": 17,
                            "lenght": 3,
                            "name": "Test End Line",
                            "value_type": "fixed",
                            "value": "end",
                            "need_loop": True,
                            "match_group": "A02",
                            "end_line": True,
                        },
                    ),
                ]
            }
        )

        bank_payment.bank_export_format_id = self.bank_export_format.id
        text = bank_payment._generate_bank_payment_text()
        self.assertEqual(
            text, "9999999999TESTmatch groupconditionneed loopend\r\nneed loopend\r\n"
        )

    def test_07_export_excel(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        xlsx_data = self.action_bank_export_excel(bank_payment)
        self.assertEqual(xlsx_data[1], "xlsx")
