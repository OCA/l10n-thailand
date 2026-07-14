# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from unittest.mock import MagicMock, Mock

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
        """Test xlsx report generation and structure"""
        # Create bank payment with export lines
        self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        self.create_payment_from_invoice(self.bill_partner2, post=True)

        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        self.assertEqual(len(bank_payment.export_line_ids), 2)

        # Test action_export_excel_file returns correct structure
        xlsx_data = self.action_bank_export_excel(bank_payment)
        self.assertEqual(xlsx_data["report_type"], "xlsx")
        self.assertEqual(xlsx_data["report_name"], "bank.payment.export.xlsx")

        # Test xlsx report model methods
        xlsx_report = self.env["report.bank.payment.export.xlsx"]

        # Test _get_export_payment_vals returns correct columns
        export_vals = xlsx_report._get_export_payment_vals(bank_payment)
        self.assertIn("01_sequence", export_vals)
        self.assertIn("02_reference", export_vals)
        self.assertIn("03_payment_date", export_vals)
        self.assertIn("04_partner", export_vals)
        self.assertIn("05_recipient_bank", export_vals)
        self.assertIn("06_recipient_bank_name", export_vals)
        self.assertIn("07_recipient_bank_holder_name", export_vals)
        self.assertIn("08_amount", export_vals)
        self.assertIn("09_recipient_bank_code", export_vals)
        self.assertIn("10_recipient_bank_branch_code", export_vals)

        # Test column headers
        self.assertEqual(export_vals["01_sequence"]["header"]["value"], "No.")
        self.assertEqual(export_vals["02_reference"]["header"]["value"], "Reference")
        self.assertEqual(
            export_vals["03_payment_date"]["header"]["value"], "Payment Date"
        )
        self.assertEqual(export_vals["04_partner"]["header"]["value"], "Vendor")
        self.assertEqual(
            export_vals["05_recipient_bank"]["header"]["value"], "Account Number"
        )
        self.assertEqual(
            export_vals["06_recipient_bank_name"]["header"]["value"], "Bank Name"
        )
        self.assertEqual(
            export_vals["07_recipient_bank_holder_name"]["header"]["value"],
            "Account Holder Name",
        )
        self.assertIn("Amount", export_vals["08_amount"]["header"]["value"])
        self.assertEqual(
            export_vals["09_recipient_bank_code"]["header"]["value"], "Bank Code"
        )
        self.assertEqual(
            export_vals["10_recipient_bank_branch_code"]["header"]["value"],
            "Bank Branch Code",
        )

        # Test _get_header_data_list returns bank info
        header_data_list = xlsx_report._get_header_data_list(bank_payment)
        self.assertEqual(len(header_data_list), 1)
        self.assertEqual(header_data_list[0][0], "Bank")

        # Test _get_render_space for each export line
        for idx, pe_line in enumerate(bank_payment.export_line_ids):
            render_space = xlsx_report._get_render_space(idx, pe_line, bank_payment)
            self.assertIn("sequence", render_space)
            self.assertIn("reference", render_space)
            self.assertIn("payment_date", render_space)
            self.assertIn("partner", render_space)
            self.assertIn("acc_number", render_space)
            self.assertIn("bank_name", render_space)
            self.assertIn("acc_holder_name", render_space)
            self.assertIn("amount", render_space)
            self.assertIn("bank_code", render_space)
            self.assertIn("bank_branch_code", render_space)
            # Verify sequence is 1-based
            self.assertEqual(render_space["sequence"], idx + 1)
            # Verify amount matches payment amount
            self.assertEqual(render_space["amount"], pe_line.payment_amount)

        # Test _get_ws_params returns correct structure
        ws_params_list = xlsx_report._get_ws_params(None, None, bank_payment)
        self.assertEqual(len(ws_params_list), 1)
        ws_params = ws_params_list[0]
        self.assertEqual(ws_params["ws_name"], "Export Payment Excel Report")
        self.assertEqual(ws_params["generate_ws_method"], "_export_payment_report")
        self.assertIn("wanted_list", ws_params)
        self.assertIn("col_specs", ws_params)
        # Verify all 10 columns are in wanted_list
        self.assertEqual(len(ws_params["wanted_list"]), 10)

        mock_wb = Mock()
        mock_ws = MagicMock()

        row_pos = xlsx_report._export_payment_report(
            mock_wb, mock_ws, ws_params, None, bank_payment
        )
        self.assertGreater(row_pos, 0)

    def test_08_receiver_branch_code_gsb(self):
        """Test _get_receiver_branch_code_gsb for 12 and 15 digit account numbers"""
        # Create GSB bank and a partner bank, then attach it to a real payment so
        # that the required payment_id constraint on bank.payment.export.line is
        # met. payment_partner_bank_id is a related field of payment_id, hence it
        # is set on the payment rather than directly on the export line.
        bank_gsb = self.env["res.bank"].create(
            {
                "name": "GSB",
                "bic": "GSBATHBK",
                "bank_code": "030",
            }
        )
        partner_bank = self.create_partner_bank(
            "123456789012", self.partner_1, bank_gsb
        )
        payment = self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        payment.partner_bank_id = partner_bank.id
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        export_line = self.env["bank.payment.export.line"].create(
            {
                "payment_export_id": bank_payment.id,
                "payment_id": payment.id,
            }
        )

        # 12 digits: branch code = "999" + first digit
        partner_bank.acc_number = "123456789012"
        self.assertEqual(export_line._get_receiver_branch_code_gsb(), "9991")

        # 15 digits: branch code = first 4 digits
        partner_bank.acc_number = "123456789012345"
        self.assertEqual(export_line._get_receiver_branch_code_gsb(), "1234")

    def test_09_onchange_profile_id(self):
        """Test _onchange_profile_id updates fields from profile"""
        # Create profile with effective_date field
        field_effective_date = self.field_model.search(
            [("name", "=", "effective_date"), ("model", "=", "bank.payment.export")]
        )
        field_bank = self.field_model.search(
            [("name", "=", "bank"), ("model", "=", "bank.payment.export")]
        )
        profile = self.create_bank_payment_profile(
            "TEST",
            [
                {"field_id": field_bank.id, "value": "TEST"},
                {"field_id": field_effective_date.id, "value": "2099-12-31"},
            ],
        )
        # Create bank payment without profile
        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        self.assertFalse(bank_payment.profile_id)
        self.assertFalse(bank_payment.effective_date)

        # Set profile and trigger onchange
        bank_payment.profile_id = profile
        bank_payment._onchange_profile_id()

        # Verify fields updated from profile
        self.assertEqual(bank_payment.bank, "TEST")
        self.assertEqual(str(bank_payment.effective_date), "2099-12-31")

    def test_10_data_level_functions(self):
        """Test data level functions: payment, invoice, wht, custom"""
        # Create payments
        self.create_payment_from_invoice(self.bill_partner1_1, post=True)
        self.create_payment_from_invoice(self.bill_partner2, post=True)

        bank_payment = self.bank_payment_export_model.create({"name": "/"})
        bank_payment.action_get_all_payments()
        active_lines = bank_payment.export_line_ids
        self.assertEqual(len(active_lines), 2)

        # Test _get_data_level_payment
        payment_items = bank_payment._get_data_level_payment(active_lines, {})
        self.assertEqual(len(payment_items), 2)
        self.assertIn("line", payment_items[0])
        self.assertIn("payment", payment_items[0])
        self.assertIn("invoices", payment_items[0])

        # Test _get_data_level_invoice
        invoice_items = bank_payment._get_data_level_invoice(active_lines, {})
        self.assertGreater(len(invoice_items), 0)
        self.assertIn("invoice", invoice_items[0])
        self.assertIn("idx_invoice", invoice_items[0])

        # Test _get_data_level_wht
        wht_items = bank_payment._get_data_level_wht(active_lines, {})
        self.assertGreater(len(wht_items), 0)
        self.assertIn("wht_cert", wht_items[0])
        self.assertIn("idx_wht", wht_items[0])

        # Test _get_data_level_custom with simple iterable
        group = {
            "data_level": "custom",
            "custom_iterable": "[1, 2, 3]",
        }
        custom_items = bank_payment._get_data_level_custom(active_lines, group)
        # 2 lines × 3 items = 6 items
        self.assertEqual(len(custom_items), 6)
        self.assertIn("sub_line", custom_items[0])
        self.assertIn("idx_sub_line", custom_items[0])
