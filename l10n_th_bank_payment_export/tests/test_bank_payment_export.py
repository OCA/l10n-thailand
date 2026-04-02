# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form

from .common import CommonBankPaymentExport


class TestBankPaymentExport(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup Profile (default field values, e.g. effective_date)
        field_effective_date = cls.field_model.search(
            [("name", "=", "effective_date"), ("model", "=", "bank.payment.export")]
        )
        data_dict = [
            {
                "field_id": field_effective_date.id,
                "value": "9999-01-01",
            }
        ]
        cls.profile_test_bank = cls.create_bank_payment_profile(cls, "TEST", data_dict)

        # Setup Bank Template (text file structure)
        cls.bank_template = cls.create_bank_template(
            cls,
            "TEST",
            [
                {
                    "sequence": 10,
                    "field_length": 10,
                    "name": "Test Line1",
                    "source_type": "fixed",
                    "fixed_value": "9999999999",
                },
                {
                    "sequence": 11,
                    "field_length": 4,
                    "name": "Test Line2",
                    "source_type": "fixed",
                    "fixed_value": "TEST",
                },
            ],
        )

    def test_01_bank_template_line_position(self):
        """Bank template lines compute their running position from field_length."""
        template = self.bank_template
        # Position is computed from the running field_length (1-based).
        self.assertEqual(template.template_line_ids[0].position_from, 1)
        self.assertEqual(template.template_line_ids[0].position_to, 10)
        self.assertEqual(len(template.template_line_ids), 2)

        # Adding a line keeps the running position; each line accumulates the
        # previous position regardless of its sequence value.
        template.write(
            {
                "template_line_ids": [
                    Command.create(
                        {
                            "sequence": 11,
                            "field_length": 4,
                            "name": "Test Line2",
                            "source_type": "fixed",
                            "fixed_value": "TEST",
                        },
                    )
                ]
            }
        )
        self.assertEqual(len(template.template_line_ids), 3)
        self.assertEqual(template.template_line_ids[1].position_from, 11)
        # Line[2] accumulates after line[1] (11..14), so position_from = 15.
        self.assertEqual(template.template_line_ids[2].position_from, 15)

        # A line_section display_type resets the running position to 1.
        template.write(
            {
                "template_line_ids": [
                    Command.create(
                        {
                            "sequence": 12,
                            "field_length": 4,
                            "name": "Test Section",
                            "display_type": "line_section",
                        },
                    ),
                    Command.create(
                        {
                            "sequence": 13,
                            "field_length": 4,
                            "name": "Test After Section",
                            "source_type": "fixed",
                            "fixed_value": "TEST",
                        },
                    ),
                ]
            }
        )
        self.assertEqual(len(template.template_line_ids), 5)
        # The line right after the section resets to position_from = 1.
        self.assertEqual(template.template_line_ids[-1].position_from, 1)

        # It should error, when fixed_value is longer than field_length.
        with self.assertRaises(UserError):
            template.template_line_ids.write(
                {
                    "field_length": 5,
                    "fixed_value": "123456",
                }
            )

    def test_02_create_payment_default_exported(self):
        """
        Check export status on payment when checked button 'Bank Payment Exported'
        on register payment wizard
        """
        # Make payment with exported
        payment1 = (
            self.register_payments_model.with_context(
                active_model="account.move", active_ids=self.bill_partner1_1.ids
            )
            .create({"payment_date": self.bill_partner1_1.date, "is_export": True})
            ._create_payments()
        )

        self.assertEqual(payment1.export_status, "exported")
        self.assertFalse(payment1.payment_export_id)

        # Make payment without exported
        payment2 = (
            self.register_payments_model.with_context(
                active_model="account.move", active_ids=self.bill_partner1_2.ids
            )
            .create({"payment_date": self.bill_partner1_2.date})
            ._create_payments()
        )

        self.assertEqual(payment2.export_status, "draft")
        self.assertFalse(payment2.payment_export_id)
        self.assertEqual(payment2.state, "paid")

    def test_03_create_bank_payment_export_from_payment(self):
        """Create bank payment export from vendor payment"""

        bill_partner1_3 = self.init_invoice(
            "in_invoice",
            partner=self.partner_1,
            amounts=[100.0],
            post=True,
        )

        payment1 = self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        payment2 = self.create_payment_from_invoice(bill_partner1_3, post=True)
        payment2_exported = self.create_payment_from_invoice(self.bill_partner1_2)
        payment2_exported.write({"is_export": True})
        payment2_exported = payment2_exported._create_payments()
        payment3 = self.create_payment_from_invoice(
            self.bill_partner1_currency, post=True
        )
        payment4 = self.create_payment_from_invoice(self.bill_partner2, post=True)

        # Not active_ids, it should return False
        action = self.bank_payment_export_model.with_context(
            active_model="account.payment"
        ).action_create_bank_payment_export()
        self.assertFalse(action)

        # Not allow export if payment is exported.
        with self.assertRaisesRegex(UserError, "have already been exported:"):
            self.bank_payment_export_model.with_context(
                active_model="account.payment",
                active_ids=payment2_exported.ids,
            ).action_create_bank_payment_export()

        payment4.action_draft()
        self.assertEqual(payment4.state, "draft")

        # Not allow export if payment is not paid.
        with self.assertRaisesRegex(
            UserError, "You can only export bank payments in state 'paid'"
        ):
            self.bank_payment_export_model.with_context(
                active_model="account.payment",
                active_ids=payment4.ids,
            ).action_create_bank_payment_export()

        # Allow payment with same currency only
        with self.assertRaisesRegex(
            UserError, "You can export bank payments with 1 currency only."
        ):
            self.bank_payment_export_model.with_context(
                active_model="account.payment",
                active_ids=(payment1 + payment3).ids,
            ).action_create_bank_payment_export()

        # The journal bank BIC must be a bank supported by an installed
        # payment-export module.
        bank_journal = (payment1 + payment2).mapped("journal_id")
        bank_journal.bank_id = self.bank_ing.id
        bank_journal.bank_id.bic = "TEST"
        action = self.bank_payment_export_model.with_context(
            active_model="account.payment",
            active_ids=(payment1 + payment2).ids,
        ).action_create_bank_payment_export()
        self.assertEqual(len(action["context"]["default_export_line_ids"]), 2)
        self.assertEqual(action["context"]["default_bank"], "TEST")

        # Unsupported BIC must raise an error.
        bank_journal.bank_id.bic = "UNKNOWNBIC"
        with self.assertRaisesRegex(UserError, "No payment export format"):
            self.bank_payment_export_model.with_context(
                active_model="account.payment",
                active_ids=(payment1 + payment2).ids,
            ).action_create_bank_payment_export()

        bank_journal.bank_id.bic = "TEST"
        action = self.bank_payment_export_model.with_context(
            active_model="account.payment",
            active_ids=(payment1 + payment2).ids,
        ).action_create_bank_payment_export()
        self.assertEqual(action["context"]["default_bank"], "TEST")
        defaults = self.bank_payment_export_model.with_context(
            **action["context"]
        ).default_get(["bank"])
        self.assertEqual(defaults["bank"], "TEST")

    def test_04_common_function(self):
        """Check other module can call common function and get this result"""

        payment1 = self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        self.create_payment_from_invoice(self.bill_partner1_2, post=True)
        self.create_payment_from_invoice(self.bill_partner1_currency, post=True)
        self.create_payment_from_invoice(self.bill_partner2, post=True)
        self.create_payment_from_invoice(self.inv_partner1, post=True)

        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertFalse(bank_payment.export_line_ids)
        bank_payment.action_get_all_payments()
        # Payment1, 2 and 4
        self.assertEqual(len(bank_payment.export_line_ids.ids), 3)

        # Test bank difference bank payment
        with self.assertRaisesRegex(
            UserError,
            "You can not selected bank difference with bank journal on payment.",
        ):
            bank_payment.export_line_ids[
                0
            ].payment_journal_id.bank_id = self.bank_ing.id
            bank_payment.bank = "TEST"
            bank_payment.check_bank_payment()

        with self.assertRaisesRegex(
            UserError, "Effective Date must be more than or equal"
        ):
            bank_payment.effective_date = "2020-01-01"  # check back date

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

        # Test get address with length max 99
        address = bank_payment._get_address(payment1.partner_id, 99)
        self.assertIn(payment1.partner_id.street, address)

    def test_05_create_bank_payment_export_direct(self):
        # Register 5 Payment
        self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        self.create_payment_from_invoice(self.bill_partner1_2, post=True)
        self.create_payment_from_invoice(self.bill_partner1_currency, post=True)
        self.create_payment_from_invoice(self.bill_partner2, post=True)
        self.create_payment_from_invoice(self.inv_partner1, post=True)

        # 1. Test delete document with state draft
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertNotEqual(bank_payment.name, "/")
        self.assertEqual(len(bank_payment.export_line_ids), 0)
        self.assertEqual(bank_payment.state, "draft")
        self.assertFalse(bank_payment.bank)
        with Form(bank_payment) as pe:
            pe.profile_id = self.profile_test_bank
            pe.bank_template_id = self.bank_template
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
        with self.assertRaisesRegex(
            UserError, "You need to add a line before confirm."
        ):
            bank_payment.action_confirm()

        # 4. Get all payment and check default payment
        #     - payment1
        #     - payment2
        #     - payment4
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 3)

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
        self.assertEqual(bank_payment.state, "confirm")
        export_line[2].action_reject()
        self.assertEqual(export_line[2].state, "reject")
        self.assertEqual(export_line[1].state, bank_payment.state)
        self.assertEqual(len(set(export_line.mapped("state"))), 1)

        # 7. Test delete document with state is not draft
        with self.assertRaisesRegex(
            UserError, "You are trying to delete a record state is not 'draft'"
        ):
            bank_payment.unlink()

    def test_06_export_text_file(self):
        # Register 5 Payment
        self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        self.create_payment_from_invoice(self.bill_partner1_2, post=True)
        self.create_payment_from_invoice(self.bill_partner1_currency, post=True)
        self.create_payment_from_invoice(self.bill_partner2, post=True)
        self.create_payment_from_invoice(self.inv_partner1, post=True)

        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 3)

        # Test Export Text File (No bank)
        text_list = bank_payment.action_export_text_file()
        self.assertEqual(bank_payment.state, "done")
        self.assertEqual(text_list["report_type"], "qweb-text")
        text_word = bank_payment._export_bank_payment_text_file()
        self.assertEqual(
            text_word,
            "Demo Text File. You must config `Bank Template` First.",
        )

        # It should error, when generate text file without bank template
        self.assertFalse(bank_payment.bank_template_id)
        with self.assertRaisesRegex(UserError, "Bank format not found."):
            bank_payment._generate_bank_payment_text()

        # Build a template that exercises sections + payment data level looping.
        # The export has 3 active (non-rejected) lines, so a "payment" data-level
        # section repeats its lines once per export line.
        section_model = self.env["bank.template.section"]
        payment_section = section_model.create(
            {
                "name": "Per Payment",
                "sequence": 20,
                "data_level": "payment",
            }
        )
        loop_template = self.bank_template_model.create(
            {
                "name": "Test Loop Template",
                "bank": "TEST",
                "line_ending": "crlf",
                "template_line_ids": [
                    Command.create(
                        {
                            "sequence": 10,
                            "field_length": 10,
                            "name": "Fixed Header",
                            "source_type": "fixed",
                            "fixed_value": "9999999999",
                        },
                    ),
                    # Line inside the payment section: repeat per export line.
                    Command.create(
                        {
                            "sequence": 20,
                            "field_length": 6,
                            "name": "Per Payment",
                            "section_id": payment_section.id,
                            "source_type": "fixed",
                            "fixed_value": "loop",
                        },
                    ),
                ],
            }
        )

        bank_payment.bank_template_id = loop_template.id
        text = bank_payment._generate_bank_payment_text()
        # Header line first (sequence 10 < section sequence 20), then the
        # payment-level section repeats once per active export line (3 times).
        # "loop" is left-justified to field_length 6 -> "loop  ".
        self.assertEqual(
            text,
            "9999999999" + "\r\n" + ("loop  " + "\r\n") * 3,
        )

    def test_07_export_excel(self):
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.action_bank_export_excel(bank_payment)
