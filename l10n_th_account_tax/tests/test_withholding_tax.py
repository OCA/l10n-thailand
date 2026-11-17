# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from ast import literal_eval

from freezegun import freeze_time
from lxml import html as lxml_html

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import new_test_user

from .common import ThAccountTaxCommon

DATE = "2026-01-01"


@tagged("post_install", "-at_install")
@freeze_time(DATE)
class TestWithholdingTax(ThAccountTaxCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env["wht.report"]
        cls.code_model = cls.env["withholding.tax.code.income"]
        cls.other_wht_payable_account = cls._create_account(
            "Other Withholding Tax Payable Test", "215101", "liability_current"
        )
        cls.vat_tax = cls.company_data["default_tax_purchase"]
        cls.purchase_tax = cls._create_wht_tax("WHT Purchase Service 3%", amount=-3.0)
        cls.rent_tax = cls._create_wht_tax("WHT Purchase Rent 5%", amount=-5.0)
        cls.sale_tax = cls._create_wht_tax("WHT Sale Customer 3%", type_tax_use="sale")
        cls.other_tax = cls._create_wht_tax(
            "WHT Other 1%",
            amount=-1.0,
            income_tax_type="others",
            l10n_th_income_tax_type_others="Lottery",
        )
        cls.group_child_tax = cls._create_wht_tax("WHT Group Child Service 3%")
        cls.group_tax = cls.env["account.tax"].create(
            {
                "name": "WHT Group Single Child",
                "amount_type": "group",
                "type_tax_use": "purchase",
                "children_tax_ids": [Command.set(cls.group_child_tax.ids)],
            }
        )
        cls.split_tax = cls._create_wht_tax(
            "WHT Split Repartition Service 3%",
            tax_accounts=[
                (cls.wht_payable_account, 50.0),
                (cls.other_wht_payable_account, 50.0),
            ],
        )

    def _create_vendor_bill(
        self, amount=1000.0, partner=None, tax=None, move_type="in_invoice"
    ):
        return self._create_th_invoice(
            move_type,
            [(amount, tax or self.purchase_tax)],
            partner=partner,
            fill_tax_invoice=move_type.startswith("in_"),
        )

    def _create_multi_tax_entry(self, partner_taxes):
        """Entry with an expense of 1000 per (partner, tax) and its payable"""
        lines = []
        for partner, tax in partner_taxes:
            lines += [
                {
                    "name": "Service expense",
                    "partner_id": partner.id,
                    "account_id": self.expense_account.id,
                    "debit": 1000.0,
                    "tax_ids": [Command.set(tax.ids)],
                },
                {
                    "name": "Net payable",
                    "partner_id": partner.id,
                    "account_id": self.payable_account.id,
                    "credit": 1000.0 * (1.0 + tax.amount / 100.0),
                },
            ]
        return self._create_entry(lines)

    def _get_tawi_checked_boxes(self, html):
        """Titles of the checked boxes of a 50 Tawi report"""
        tree = lxml_html.fromstring(html)
        return [
            title.replace("\u200b", "").strip()
            for title in tree.xpath(
                "//div[span[normalize-space()='✓']]/following-sibling::span/text()"
            )
        ]

    def test_01_create_payment_withholding_tax(self):
        """Pay a vendor bill with withholding tax, create and confirm its
        certificate, and report the payment."""
        # Default income code, one per income tax form and type of income
        default_code = self.code_model.create(
            {
                "name": "Test Default Income Code PND3",
                "code": "TDEF3",
                "income_tax_form": "pnd3",
                "wht_cert_income_type": "5",
                "is_default": True,
            }
        )
        with self.assertRaisesRegex(
            UserError, r"You can not default field 'PND3 - 5\. .*' more than 1\."
        ):
            self.code_model.create(
                {
                    "name": "Test Duplicate Default Income Code PND3",
                    "code": "TDUP3",
                    "income_tax_form": "pnd3",
                    "wht_cert_income_type": "5",
                    "is_default": True,
                }
            )
        other_codes = self.code_model.create(
            [
                {
                    "name": f"Test Income Code {form} {income_type}",
                    "code": f"T{form}{income_type}",
                    "income_tax_form": form,
                    "wht_cert_income_type": income_type,
                }
                for form, income_type in (
                    ("pnd53", "5"),
                    ("pnd3", "6"),
                    ("pnd3", "5"),
                )
            ]
        )
        with self.assertRaisesRegex(UserError, "You can not default field"):
            other_codes.write({"is_default": True})
        other_codes[:2].write({"is_default": True})
        self.assertEqual(other_codes.mapped("is_default"), [True, True, False])

        bill = self._create_vendor_bill()
        bill.action_post()
        self.assertEqual(bill.state, "posted")
        self.assertFalse(bill.line_ids.filtered("tax_line_id.is_withholding_tax"))
        self.assertEqual(bill.withholding_total_amount_currency, 30.0)
        # Certificates are created from the payment, not from the bill
        with self.assertRaises(UserError):
            bill.create_wht_cert()
        self.assertFalse(bill.wht_cert_ids)

        wizard = self._create_payment_register(bill, withhold="withhold_pay")
        self.assertRecordValues(
            wizard.withholding_line_ids,
            [{"tax_id": self.purchase_tax.id, "base_amount": 1000.0, "amount": 30.0}],
        )
        payment = wizard._create_payments()
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.state, "paid")
        self.assertEqual(payment.move_id.state, "posted")
        self.assertTrue(payment.has_wht)
        self.assertEqual(payment.wht_cert_status, "none")
        moves = self.env["account.move"].search(
            [("has_wht", "=", True), ("wht_cert_ids", "=", False)]
        )
        self.assertIn(payment.move_id, moves)

        action = payment.action_create_wht_cert()
        cert = payment.wht_cert_ids
        self.assertEqual(len(cert), 1)
        self.assertIsInstance(action, dict)
        self.assertIn(("id", "in", cert.ids), action["domain"])
        self.assertEqual(payment.wht_certs_count, 1)
        self.assertEqual(payment.wht_cert_ids, payment.move_id.wht_cert_ids)
        self.assertEqual(payment.wht_cert_status, "draft")
        self.assertEqual(payment.move_id.wht_cert_status, "draft")
        self.assertEqual(cert.number, "/")
        self.assertEqual(cert.name, payment.name)
        self.assertEqual(cert.date, payment.date)
        self.assertRecordValues(
            cert,
            [
                {
                    "partner_id": self.partner_a.id,
                    "payment_id": payment.id,
                    "move_id": payment.move_id.id,
                    "income_tax_form": "pnd3",
                    "tax_payer": "withholding",
                    "state": "draft",
                }
            ],
        )
        self.assertRecordValues(
            cert.wht_line,
            [
                {
                    "wht_tax_id": self.purchase_tax.id,
                    "base": 1000.0,
                    "amount": 30.0,
                    "wht_percent": 3.0,
                    "wht_cert_income_type": "5",
                    "wht_cert_income_code": default_code.id,
                }
            ],
        )
        self.assertTrue(cert.wht_line.wht_cert_income_desc)
        self.assertIn(
            ("id", "in", payment.wht_cert_ids.ids),
            payment.button_wht_certs()["domain"],
        )
        with self.assertRaisesRegex(
            UserError, "There is no withholding tax certificate to create."
        ):
            payment.move_id.create_wht_cert()
        self.assertEqual(payment.move_id.wht_cert_ids, cert)

        # A plain internal user reads the certificate and its income code only
        user = new_test_user(
            self.env, login="th_wht_cert_reader", groups="base.group_user"
        )
        cert_as_user = cert.with_user(user)
        self.assertEqual(cert_as_user.partner_id, self.partner_a)
        self.assertEqual(cert_as_user.wht_line.amount, 30.0)
        self.assertEqual(cert_as_user.wht_line.wht_cert_income_code.code, "TDEF3")
        with self.assertRaises(AccessError):
            cert_as_user.write({"income_tax_form": "pnd53"})
        with self.assertRaises(AccessError):
            cert_as_user.wht_line.write({"amount": 1.0})
        with self.assertRaises(AccessError):
            cert_as_user.wht_line.wht_cert_income_code.write({"name": "Changed"})

        # Type of income is required to confirm, e.g. not set for dividends
        cert.wht_line.wht_cert_income_type = False
        with self.assertRaises(UserError):
            cert.action_done()
        self.assertEqual(cert.number, "/")
        with Form(cert.wht_line) as line:
            line.wht_cert_income_type = "5"
        self.assertEqual(cert.wht_line.wht_cert_income_code, default_code)

        cert.action_done()
        self.assertEqual(cert.state, "done")
        self.assertNotEqual(cert.number, "/")
        self.assertEqual(cert.verify_by, self.env.user)
        self.assertEqual(payment.wht_cert_status, "done")
        number = cert.number
        cert.action_draft()
        self.assertEqual(cert.state, "draft")
        self.assertEqual(cert.number, number)
        self.assertFalse(cert.verify_by)
        cert.action_done()
        self.assertEqual(cert.number, number)
        cert.action_cancel()
        self.assertEqual(cert.state, "cancel")
        self.assertEqual(payment.wht_cert_status, "cancel")
        self.assertFalse(cert.verify_by)

        action = payment.action_create_wht_cert()
        new_cert = payment.wht_cert_ids - cert
        self.assertEqual(len(new_cert), 1)
        self.assertEqual(new_cert.state, "draft")
        self.assertEqual(cert.state, "cancel")
        self.assertEqual(payment.move_id.wht_cert_ids, cert | new_cert)
        self.assertEqual(payment.wht_cert_status, "draft")
        self.assertIn(("id", "in", payment.wht_cert_ids.ids), action["domain"])

        # Withholding tax report of the payment, not of the bill
        report_rows = self.report_model.search([("move_id", "=", payment.move_id.id)])
        self.assertEqual(len(report_rows), 2)
        self.assertNotIn(bill.id, report_rows.mapped("move_id").ids)
        wh_base_lines = payment.move_id.line_ids.filtered(
            lambda line: line.account_id == self.wht_base_account and not line.tax_ids
        )
        self.assertTrue(wh_base_lines)
        self.assertNotIn(wh_base_lines.id, report_rows.ids)
        self.assertEqual(sum(report_rows.mapped("amount_income")), 1000.0)
        self.assertRecordValues(
            report_rows.sorted("line_type"),
            [
                {
                    "move_id": payment.move_id.id,
                    "payment_id": payment.id,
                    "journal_id": payment.move_id.journal_id.id,
                    "partner_id": self.partner_a.id,
                    "tax_id": self.purchase_tax.id,
                    "type_tax_use": "purchase",
                    "is_pit": False,
                    "line_type": "base",
                    "calendar_year": "2026",
                    "amount_income": 1000.0,
                    "amount_wht": 0.0,
                },
                {
                    "move_id": payment.move_id.id,
                    "payment_id": payment.id,
                    "journal_id": payment.move_id.journal_id.id,
                    "partner_id": self.partner_a.id,
                    "tax_id": self.purchase_tax.id,
                    "type_tax_use": "purchase",
                    "is_pit": False,
                    "line_type": "tax",
                    "calendar_year": "2026",
                    "amount_income": 0.0,
                    "amount_wht": 30.0,
                },
            ],
        )
        wht_action = self.env.ref("l10n_th_account_tax.action_wht_report")
        self.assertEqual(
            literal_eval(wht_action.context).get("search_default_purchase"), 1
        )
        pit_action = self.env.ref("l10n_th_account_tax.action_pit_report")
        self.assertEqual(literal_eval(pit_action.domain), [("is_pit", "=", True)])
        partner_action = self.partner_a.action_view_pit_income()
        self.assertIn(("is_pit", "=", True), partner_action["domain"])

    def test_02_create_payment_withholding_tax_partial_and_condition(self):
        """Partial payments certify their prorated amounts, a withholding only
        payment the full amount, and the tax payer of the certificates comes
        from the withholding condition of the payment."""
        bill = self._create_vendor_bill()
        bill.action_post()
        payments = self.env["account.payment"]
        for installment, condition, tax_payer in (
            (0, "forever", "paid_continue"),
            (1, "one_time", "paid_one_time"),
        ):
            wizard = self._create_payment_register(
                bill, withhold="withhold_pay", l10n_th_wth_condition=condition
            )
            if installment == 0:
                wizard.amount = 500.0
            self.assertAlmostEqual(wizard.amount, 500.0)
            self.assertRecordValues(
                wizard.withholding_line_ids,
                [
                    {
                        "tax_id": self.purchase_tax.id,
                        "comodel_percentage_paid_factor": 0.5,
                        "base_amount": 500.0,
                        "amount": 15.0,
                    }
                ],
            )
            payment = wizard._create_payments()
            self.assertEqual(len(payment), 1)
            self.assertEqual(payment.move_id.state, "posted")
            self.assertEqual(payment.l10n_th_wth_condition, condition)
            self.assertNotIn(payment, payments)
            payments |= payment
            cert = payment.move_id.create_wht_cert()
            self.assertEqual(len(cert), 1)
            self.assertEqual(cert.tax_payer, tax_payer)
            self.assertRecordValues(
                cert.wht_line,
                [{"wht_tax_id": self.purchase_tax.id, "base": 500.0, "amount": 15.0}],
            )
            self.assertAlmostEqual(bill.amount_residual, 500.0 * (1 - installment))
        self.assertEqual(len(payments.move_id.wht_cert_ids), 2)

        # Withholding only, without liquidity
        bill = self._create_vendor_bill()
        bill.action_post()
        wizard = self._create_payment_register(bill, withhold="withhold")
        self.assertAlmostEqual(wizard.amount, 30.0)
        self.assertRecordValues(
            wizard.withholding_line_ids,
            [{"tax_id": self.purchase_tax.id, "base_amount": 1000.0, "amount": 30.0}],
        )
        payment = wizard._create_payments()
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.move_id.state, "posted")
        self.assertEqual(payment.journal_id.type, "general")
        liquidity_lines, _counterpart_lines, _writeoff_lines = payment._seek_for_lines()
        self.assertFalse(liquidity_lines)
        cert = payment.move_id.create_wht_cert()
        self.assertEqual(len(cert), 1)
        self.assertEqual(cert.tax_payer, "withholding")
        self.assertRecordValues(
            cert.wht_line,
            [{"wht_tax_id": self.purchase_tax.id, "base": 1000.0, "amount": 30.0}],
        )

    def test_03_withholding_tax_customer_invoice(self):
        """A customer payment reports sale withholding with positive amounts,
        without certificate."""
        invoice = self._create_th_invoice("out_invoice", [(1000.0, self.sale_tax)])
        invoice.action_post()
        payment = self._pay(invoice, withhold="withhold_pay", inbound=True)
        self.assertFalse(payment.has_wht)
        self.assertFalse(payment.wht_cert_status)
        self.assertFalse(payment.move_id.has_wht)
        self.assertFalse(payment.move_id.wht_cert_status)
        rows = self.report_model.search([("move_id", "=", payment.move_id.id)])
        self.assertEqual(len(rows), 2)
        self.assertRecordValues(
            rows.sorted("line_type"),
            [
                {
                    "move_id": payment.move_id.id,
                    "payment_id": payment.id,
                    "tax_id": self.sale_tax.id,
                    "type_tax_use": "sale",
                    "is_pit": False,
                    "line_type": "base",
                    "amount_income": 1000.0,
                    "amount_wht": 0.0,
                },
                {
                    "move_id": payment.move_id.id,
                    "payment_id": payment.id,
                    "tax_id": self.sale_tax.id,
                    "type_tax_use": "sale",
                    "is_pit": False,
                    "line_type": "tax",
                    "amount_income": 0.0,
                    "amount_wht": 30.0,
                },
            ],
        )

    def test_04_withholding_tax_multi_partner(self):
        """Certificates are created per partner and income tax form, from the
        PND tax tags of the tax or else from the commercial partner, and only
        for the taxes without an active certificate."""
        move = self._create_tax_entry(
            self.purchase_tax, [(self.partner_a, 1000.0), (self.partner_b, 500.0)]
        )
        move.action_post()
        wht_lines = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.purchase_tax
        )
        self.assertEqual(len(wht_lines), 2)
        for partner, balance in ((self.partner_a, -30.0), (self.partner_b, -15.0)):
            self.assertRecordValues(
                wht_lines.filtered_domain([("partner_id", "=", partner.id)]),
                [
                    {
                        "partner_id": partner.id,
                        "account_id": self.wht_payable_account.id,
                        "balance": balance,
                    }
                ],
            )
        certs = move.create_wht_cert()
        self.assertEqual(len(certs), 2)
        for partner, form, base, amount in (
            (self.partner_a, "pnd3", 1000.0, 30.0),
            (self.partner_b, "pnd53", 500.0, 15.0),
        ):
            cert = certs.filtered_domain([("partner_id", "=", partner.id)])
            self.assertRecordValues(
                cert, [{"partner_id": partner.id, "income_tax_form": form}]
            )
            self.assertRecordValues(
                cert.wht_line,
                [{"wht_tax_id": self.purchase_tax.id, "base": base, "amount": amount}],
            )
        with self.assertRaisesRegex(
            UserError, "There is no withholding tax certificate to create."
        ):
            move.create_wht_cert()
        # A cancelled certificate is created again, only for its partner
        cert_a = certs.filtered(lambda cert: cert.partner_id == self.partner_a)
        cert_b = certs - cert_a
        cert_a.action_cancel()
        self.assertEqual(move.wht_cert_status, "draft")
        new_cert = move.create_wht_cert()
        self.assertEqual(new_cert.partner_id, self.partner_a)
        self.assertRecordValues(
            new_cert.wht_line,
            [{"wht_tax_id": self.purchase_tax.id, "base": 1000.0, "amount": 30.0}],
        )
        self.assertEqual(move.wht_cert_ids, certs | new_cert)
        self.assertEqual(cert_b.state, "draft")

        # Income tax form from PND tax tags, type of income from the tax
        commission_tax = self._create_wht_tax(
            "WHT Commission 3%", income_tax_type="commission"
        )
        commission_tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).tag_ids = self.env.ref("l10n_th.tag_th_pnd53")
        royalty_tax = self._create_wht_tax(
            "WHT Royalties 3%", income_tax_type="royalties"
        )
        royalty_tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "base"
        ).tag_ids = self.env.ref("l10n_th_account_tax.tag_th_income_pnd2")
        contact_b = self.env["res.partner"].create(
            {"name": "Contact B", "parent_id": self.partner_b.id}
        )
        move = self._create_multi_tax_entry(
            [
                (self.partner_a, self.purchase_tax),
                (self.partner_a, commission_tax),
                (self.partner_a, royalty_tax),
                (self.partner_a, self.rent_tax),
                (contact_b, self.other_tax),
            ]
        )
        move.action_post()
        certs = move.create_wht_cert()
        self.assertEqual(len(certs), 4)
        for partner, form, taxes, income_types, desc in (
            (self.partner_a, "pnd3", self.purchase_tax | self.rent_tax, ["5"], False),
            (self.partner_a, "pnd53", commission_tax, ["2"], False),
            (self.partner_a, "pnd2", royalty_tax, ["3"], False),
            (contact_b, "pnd53", self.other_tax, ["6"], "Lottery"),
        ):
            cert = certs.filtered(
                lambda c, p=partner, f=form: (
                    c.partner_id == p and c.income_tax_form == f
                )
            )
            self.assertEqual(len(cert), 1)
            self.assertEqual(cert.wht_line.wht_tax_id, taxes)
            self.assertEqual(
                sorted(set(cert.wht_line.mapped("wht_cert_income_type"))),
                income_types,
            )
            if desc:
                self.assertEqual(cert.wht_line.wht_cert_income_desc, desc)
        # The income tax form changed on a draft certificate, no duplicate
        certs.filtered(lambda c: c.wht_line.wht_tax_id == commission_tax).write(
            {"income_tax_form": "pnd3"}
        )
        with self.assertRaisesRegex(
            UserError, "There is no withholding tax certificate to create."
        ):
            move.create_wht_cert()
        # A tax removed from a certificate is created again, alone
        cert_a = certs.filtered(lambda c: self.rent_tax in c.wht_line.wht_tax_id)
        cert_a.wht_line.filtered(lambda line: line.wht_tax_id == self.rent_tax).unlink()
        new_cert = move.create_wht_cert()
        self.assertRecordValues(
            new_cert.wht_line,
            [{"wht_tax_id": self.rent_tax.id, "base": 1000.0, "amount": 50.0}],
        )

        # Journal items without partner use the partner of the entry
        lines = [
            {
                "name": "Service expense",
                "partner_id": False,
                "account_id": self.expense_account.id,
                "debit": 1000.0,
                "tax_ids": [Command.set(self.purchase_tax.ids)],
            },
            {
                "name": "Net payable",
                "partner_id": False,
                "account_id": self.payable_account.id,
                "credit": 970.0,
            },
        ]
        move = self._create_entry(lines, partner_id=self.partner_b.id)
        move.action_post()
        base_line = move.line_ids.filtered(
            lambda line: self.purchase_tax in line.tax_ids
        )
        self.assertFalse(base_line.partner_id)
        rows = self.report_model.search([("move_id", "=", move.id)])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows.partner_id, self.partner_b)
        self.assertEqual(sum(rows.mapped("amount_income")), 1000.0)
        self.assertEqual(sum(rows.mapped("amount_wht")), 30.0)
        cert = move.create_wht_cert()
        self.assertRecordValues(
            cert, [{"partner_id": self.partner_b.id, "income_tax_form": "pnd53"}]
        )
        self.assertRecordValues(
            cert.wht_line,
            [{"wht_tax_id": self.purchase_tax.id, "base": 1000.0, "amount": 30.0}],
        )
        # Else, a partner is required
        move = self._create_entry(lines)
        move.action_post()
        self.assertFalse(move.partner_id)
        self.assertFalse(move.line_ids.partner_id)
        self.assertTrue(move.has_wht)
        self.assertEqual(move.wht_cert_status, "none")
        with self.assertRaisesRegex(
            UserError,
            "Please set a partner on journal items with withholding tax "
            "WHT Purchase Service 3%",
        ):
            move.create_wht_cert()
        self.assertFalse(move.wht_cert_ids)

    def test_05_create_wht_cert_journal(self):
        """Post a journal entry with withholding tax, create its certificate,
        reset to draft, replace the certificate, then cancel and reverse."""
        move = self._create_tax_entry(self.purchase_tax)
        wht_lines = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.purchase_tax
        )
        self.assertRecordValues(
            wht_lines,
            [
                {
                    "tax_line_id": self.purchase_tax.id,
                    "account_id": self.wht_payable_account.id,
                    "balance": -30.0,
                    "partner_id": self.partner_a.id,
                }
            ],
        )
        # A draft entry is not reported, nor certified until it is posted
        self.assertEqual(move.state, "draft")
        self.assertFalse(self.report_model.search([("move_id", "=", move.id)]))
        with self.assertRaises(UserError):
            move.create_wht_cert()
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertEqual(sum(move.line_ids.mapped("balance")), 0.0)
        self.assertTrue(move.has_wht)
        self.assertEqual(move.wht_cert_status, "none")

        action = move.action_create_wht_cert()
        cert = move.wht_cert_ids
        self.assertEqual(len(cert), 1)
        self.assertIn(("id", "in", cert.ids), action["domain"])
        self.assertEqual(move.wht_cert_status, "draft")
        self.assertRecordValues(
            cert,
            [
                {
                    "partner_id": self.partner_a.id,
                    "move_id": move.id,
                    "company_id": self.company.id,
                    "state": "draft",
                    "income_tax_form": "pnd3",
                    "tax_payer": "withholding",
                }
            ],
        )
        self.assertRecordValues(
            cert.wht_line,
            [
                {
                    "wht_tax_id": self.purchase_tax.id,
                    "base": 1000.0,
                    "amount": 30.0,
                    "wht_percent": 3.0,
                    "wht_cert_income_type": "5",
                }
            ],
        )
        self.assertTrue(cert.wht_line.wht_cert_income_desc)
        report_rows = self.report_model.search([("move_id", "=", move.id)])
        self.assertRecordValues(
            report_rows.sorted("line_type"),
            [
                {
                    "move_id": move.id,
                    "payment_id": False,
                    "tax_id": self.purchase_tax.id,
                    "line_type": "base",
                    "amount_income": 1000.0,
                    "amount_wht": 0.0,
                },
                {
                    "move_id": move.id,
                    "payment_id": False,
                    "tax_id": self.purchase_tax.id,
                    "line_type": "tax",
                    "amount_income": 0.0,
                    "amount_wht": 30.0,
                },
            ],
        )
        # Reset to draft cancels the certificate, kept on posting again
        cert.action_done()
        self.assertEqual(move.wht_cert_status, "done")
        number = cert.number
        move.button_draft()
        self.assertEqual(move.state, "draft")
        self.assertEqual(cert.state, "cancel")
        self.assertEqual(cert.number, number)
        self.assertEqual(move.wht_cert_status, "cancel")
        self.assertFalse(self.report_model.search([("move_id", "=", move.id)]))
        move.action_post()
        self.assertEqual(cert.state, "cancel")
        self.assertEqual(move.wht_cert_ids, cert)
        self.assertTrue(self.report_model.search([("move_id", "=", move.id)]))

        # Confirming a replacement certificate cancels the replaced one
        cert = move.create_wht_cert()
        cert.action_done()
        replacement = self.env["withholding.tax.cert"].create(
            {
                "move_id": move.id,
                "date": move.date,
                "partner_id": self.partner_a.id,
                "ref_wht_cert_id": cert.id,
                "income_tax_form": cert.income_tax_form,
                "wht_line": [
                    Command.create(
                        {
                            "wht_tax_id": self.purchase_tax.id,
                            "wht_cert_income_type": "5",
                            "base": 1000.0,
                            "amount": 30.0,
                        }
                    )
                ],
            }
        )
        self.assertEqual(replacement.state, "draft")
        self.assertEqual(replacement.name, move.name)
        self.assertEqual(cert.state, "done")
        replacement.action_done()
        self.assertNotEqual(replacement.number, "/")
        self.assertNotEqual(replacement.number, cert.number)
        self.assertEqual(cert.state, "cancel")
        self.assertTrue(
            any(
                f"substituted by {replacement.name}" in str(body)
                for body in cert.message_ids.mapped("body")
            )
        )
        self.assertEqual(move.wht_cert_status, "done")

        # Cancelling the entry cancels its certificates
        move.button_cancel()
        self.assertEqual(move.state, "cancel")
        self.assertEqual(replacement.state, "cancel")
        self.assertEqual(move.wht_cert_status, "cancel")

        # Reversing an entry reverses its withholding tax
        move = self._create_tax_entry(self.purchase_tax)
        move.action_post()
        reverse_move = move._reverse_moves(cancel=True)
        self.assertRecordValues(
            reverse_move.line_ids.filtered(
                lambda line: line.tax_line_id == self.purchase_tax
            ),
            [
                {
                    "tax_line_id": self.purchase_tax.id,
                    "account_id": self.wht_payable_account.id,
                    "balance": 30.0,
                    "partner_id": self.partner_a.id,
                }
            ],
        )
        # A certificate refers to an entry of its company
        company_2 = self.setup_other_company(name="TH Company 2")["company"]
        with self.assertRaisesRegex(UserError, "no company crossover"):
            self.env["withholding.tax.cert"].create(
                {
                    "move_id": move.id,
                    "date": move.date,
                    "partner_id": self.partner_a.id,
                    "company_id": company_2.id,
                    "company_partner_id": company_2.partner_id.id,
                    "income_tax_form": "pnd53",
                }
            )

    def test_06_create_withholding_tax_multi_currency(self):
        """Certificates convert the payment base and tax to company currency."""
        currency = self.setup_other_currency("EUR", rates=[(DATE, 2.0)])
        bill = self._create_vendor_bill()
        bill.write({"currency_id": currency.id, "date": DATE})
        bill.action_post()
        wizard = self._create_payment_register(
            bill,
            withhold="withhold_pay",
            currency_id=currency.id,
        )
        self.assertRecordValues(
            wizard.withholding_line_ids,
            [{"tax_id": self.purchase_tax.id, "base_amount": 1000.0, "amount": 30.0}],
        )
        payment = wizard._create_payments()
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.currency_id, currency)
        move = payment.move_id
        self.assertEqual(move.state, "posted")
        base_lines = move.line_ids.filtered(
            lambda line: self.purchase_tax in line.tax_ids
        )
        tax_lines = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.purchase_tax
        )
        cert = move.create_wht_cert()
        self.assertEqual(len(cert), 1)
        self.assertAlmostEqual(cert.wht_line.base, sum(base_lines.mapped("balance")))
        self.assertAlmostEqual(cert.wht_line.amount, -sum(tax_lines.mapped("balance")))
        self.assertRecordValues(
            cert.wht_line,
            [{"wht_tax_id": self.purchase_tax.id, "base": 500.0, "amount": 15.0}],
        )

    def test_07_refund_payment_reverse_withholding_tax(self):
        """A vendor refund reverses report totals and cannot create a certificate."""
        bill = self._create_vendor_bill()
        bill.action_post()
        bill_payment = self._pay(bill, withhold="withhold_pay")
        refund = self._create_vendor_bill(move_type="in_refund")
        refund.action_post()
        refund_wizard = self._create_payment_register(
            refund, withhold="withhold_pay", inbound=True
        )
        self.assertEqual(refund_wizard.payment_type, "inbound")
        self.assertRecordValues(
            refund_wizard.withholding_line_ids,
            [{"tax_id": self.purchase_tax.id, "base_amount": 1000.0, "amount": 30.0}],
        )
        refund_payment = refund_wizard._create_payments()
        self.assertEqual(refund_payment.payment_type, "inbound")
        move = refund_payment.move_id
        self.assertEqual(move.state, "posted")
        self.assertFalse(move.has_wht)
        self.assertFalse(refund_payment.wht_cert_status)
        base_lines = move.line_ids.filtered(
            lambda line: self.purchase_tax in line.tax_ids
        )
        tax_lines = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.purchase_tax
        )
        self.assertAlmostEqual(sum(base_lines.mapped("balance")), -1000.0)
        self.assertAlmostEqual(sum(tax_lines.mapped("balance")), 30.0)
        with self.assertRaises(UserError):
            move.create_wht_cert()
        self.assertFalse(move.wht_cert_ids)

        rows = self.report_model.search([("partner_id", "=", self.partner_a.id)])
        refund_rows = rows.filtered(lambda row: row.move_id == move)
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(rows.mapped("amount_income")), 0.0)
        self.assertEqual(sum(rows.mapped("amount_wht")), 0.0)
        self.assertEqual(bill_payment.partner_id, refund_payment.partner_id)
        self.assertRecordValues(
            refund_rows.sorted("line_type"),
            [
                {
                    "line_type": "base",
                    "tax_id": self.purchase_tax.id,
                    "amount_income": -1000.0,
                    "amount_wht": 0.0,
                },
                {
                    "line_type": "tax",
                    "tax_id": self.purchase_tax.id,
                    "amount_income": 0.0,
                    "amount_wht": -30.0,
                },
            ],
        )

    def test_08_withholding_tax_on_lines(self):
        """One withholding tax per line, with or without VAT, also in group
        taxes; split tax repartition and group taxes are certified and reported
        per withholding tax; an entry with VAT only has no withholding."""
        with Form(self.env["account.tax"]) as tax_form:
            tax_form.name = "WHT Form 3%"
            tax_form.type_tax_use = "purchase"
            tax_form.amount = 3.0
            tax_form.is_withholding_tax = True
            tax_form.l10n_th_income_tax_type = "service"
        self.assertEqual(tax_form.record.amount, -3.0)

        with self.assertRaisesRegex(
            ValidationError, "Only one withholding tax is allowed per line"
        ):
            self._create_th_invoice(
                "in_invoice",
                [(100.0, self.vat_tax | self.purchase_tax | self.rent_tax)],
                fill_tax_invoice=True,
            )
        group_tax = self.env["account.tax"].create(
            {
                "name": "WHT Group With Two Children",
                "amount_type": "group",
                "type_tax_use": "purchase",
                "children_tax_ids": [
                    Command.set((self.purchase_tax | self.rent_tax).ids)
                ],
            }
        )
        with self.assertRaisesRegex(
            ValidationError, "Only one withholding tax is allowed per line"
        ):
            self._create_th_invoice(
                "in_invoice", [(100.0, group_tax)], fill_tax_invoice=True
            )
        bill = self._create_th_invoice(
            "in_invoice",
            [
                (100.0, self.vat_tax | self.purchase_tax),
                (100.0, self.vat_tax | self.rent_tax),
            ],
            fill_tax_invoice=True,
        )
        self.assertEqual(
            bill.invoice_line_ids[0].tax_ids, self.vat_tax | self.purchase_tax
        )
        self.assertEqual(bill.invoice_line_ids[1].tax_ids, self.vat_tax | self.rent_tax)
        with self.assertRaisesRegex(
            ValidationError, "Only one withholding tax is allowed per line"
        ):
            bill.invoice_line_ids[0].write(
                {"tax_ids": [Command.link(self.rent_tax.id)]}
            )
        bill.action_post()
        self.assertEqual(bill.withholding_total_amount_currency, 8.0)

        # Two tax repartition lines, one certificate line
        move = self._create_multi_tax_entry([(self.partner_a, self.split_tax)])
        move.action_post()
        tax_lines = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.split_tax
        )
        self.assertEqual(
            tax_lines.account_id,
            self.wht_payable_account | self.other_wht_payable_account,
        )
        self.assertEqual(tax_lines.mapped("balance"), [-15.0, -15.0])
        cert = move.create_wht_cert()
        self.assertRecordValues(
            cert.wht_line,
            [{"wht_tax_id": self.split_tax.id, "base": 1000.0, "amount": 30.0}],
        )

        # Group tax reported with its withholding child tax
        move = self._create_entry(
            [
                {
                    "name": "Service expense",
                    "partner_id": self.partner_a.id,
                    "account_id": self.expense_account.id,
                    "debit": 1000.0,
                    "tax_ids": [Command.set(self.group_tax.ids)],
                },
                {
                    "name": "Net payable",
                    "account_id": self.payable_account.id,
                    "credit": 970.0,
                },
            ]
        )
        move.action_post()
        rows = self.report_model.search([("move_id", "=", move.id)])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows.tax_id, self.group_child_tax)
        self.assertEqual(
            rows.filtered(lambda row: row.line_type == "base").amount_income, 1000.0
        )

        # VAT only, its tax line and no withholding
        move = self._create_entry(
            [
                {
                    "name": "Expense with VAT",
                    "partner_id": self.partner_a.id,
                    "account_id": self.expense_account.id,
                    "debit": 1000.0,
                    "tax_ids": [Command.set(self.vat_tax.ids)],
                },
                {
                    "name": "Payable with VAT",
                    "partner_id": self.partner_a.id,
                    "account_id": self.payable_account.id,
                    "credit": 1000.0 + 1000.0 * self.vat_tax.amount / 100.0,
                },
            ]
        )
        self.assertFalse(move.line_ids.filtered("tax_line_id.is_withholding_tax"))
        self.assertEqual(
            len(move.line_ids.filtered(lambda line: line.tax_line_id == self.vat_tax)),
            1,
        )
        self._fill_tax_invoice(move)
        move.action_post()
        self.assertFalse(move.has_wht)
        self.assertFalse(move.wht_cert_status)
        moves = self.env["account.move"].search(
            [("has_wht", "=", True), ("wht_cert_ids", "=", False)]
        )
        self.assertNotIn(move, moves)

        # Dividends have no default type of income on the certificate
        self.purchase_tax.l10n_th_income_tax_type = "dividend"
        self.assertFalse(self.purchase_tax._get_wht_cert_income_type())

    def test_09_withholding_tax_non_thai_company(self):
        """Withholding tax on manual entries and certificates are for Thai
        companies only, standard does not compute it on other entries."""
        company_data = self.setup_other_company(
            name="US Company", country_id=self.env.ref("base.us").id
        )
        company = company_data["company"]
        wht_tax = self.env["account.tax"].create(
            {
                "name": "US WHT 3%",
                "amount": -3.0,
                "type_tax_use": "purchase",
                "is_withholding_tax": True,
                "company_id": company.id,
                "country_id": self.env.ref("base.us").id,
            }
        )
        entry = (
            self.env["account.move"]
            .with_company(company)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": company_data["default_journal_misc"].id,
                    "line_ids": [
                        Command.create(
                            {
                                "name": "Service expense",
                                "partner_id": self.partner_a.id,
                                "account_id": company_data[
                                    "default_account_expense"
                                ].id,
                                "debit": 1000.0,
                                "tax_ids": [Command.set(wht_tax.ids)],
                            }
                        ),
                        Command.create(
                            {
                                "name": "Payable",
                                "partner_id": self.partner_a.id,
                                "account_id": company_data[
                                    "default_account_payable"
                                ].id,
                                "credit": 1000.0,
                            }
                        ),
                    ],
                }
            )
        )
        self.assertFalse(entry.line_ids.filtered("tax_line_id"))
        entry.action_post()
        self.assertFalse(entry.has_wht)
        self.assertFalse(entry.wht_cert_status)
        with self.assertRaises(UserError):
            entry.create_wht_cert()
        # No certificate, nor personal income tax
        with self.assertRaises(ValidationError):
            self.env["withholding.tax.cert"].create(
                {
                    "partner_id": self.partner_a.id,
                    "company_id": company.id,
                    "date": DATE,
                }
            )
        with self.assertRaises(ValidationError):
            wht_tax.write({"is_pit": True, "amount": 0.0})
        self.assertTrue(self.partner_a.show_pit_income)
        self.assertFalse(self.partner_a.with_company(company).show_pit_income)

    def test_10_print_50_tawi(self):
        """Print the standard 50 Tawi from done certificates, with the payer
        signature if configured, and send it by email. Not from payments."""
        self.partner_b.write({"street": "1 Sukhumvit Road", "city": "Bangkok"})
        contact_b = self.env["res.partner"].create(
            {"name": "Accounting", "parent_id": self.partner_b.id, "type": "invoice"}
        )
        self.assertFalse(contact_b.street)
        move = self._create_multi_tax_entry(
            [
                (self.partner_a, self.purchase_tax),
                (self.partner_a, self.other_tax),
                (contact_b, self.purchase_tax),
            ]
        )
        move.action_post()
        certs = move.create_wht_cert()
        cert_a = certs.filtered(lambda cert: cert.partner_id == self.partner_a)
        cert_b = certs - cert_a
        report = self.env.ref("l10n_th_account_tax.action_report_wht_cert")
        self.assertFalse(report.binding_model_id)

        def render(cert):
            return report._render_qweb_html(report, cert.ids)[0].decode()

        def signature(cert):
            return lxml_html.fromstring(render(cert)).xpath(
                "normalize-space(//div[contains(@class, 'mt-5')]"
                "/span[contains(@class, 'position-absolute')])"
            )

        # Draft certificates are neither printed nor sent
        self.company.wht_form_print_signature = True
        self.assertFalse(signature(cert_a))
        with self.assertRaisesRegex(UserError, "done withholding tax certificate"):
            cert_a.action_send_by_email()
        with self.assertRaisesRegex(UserError, "No done withholding tax certificate"):
            certs.action_download_50_tawi_bulk()

        cert_a.write({"income_tax_form": "pnd3a", "tax_payer": "paid_one_time"})
        cert_a.action_done()
        self.assertEqual(signature(cert_a), self.env.user.name)
        self.company.wht_form_print_signature = False
        self.assertFalse(signature(cert_a))
        html = render(cert_a)
        self.assertIn(cert_a.number, html)
        # Number of the journal entry instead of the blank เล่มที่
        self.assertIn(move.name, html)
        self.assertNotIn("เล่มที่\u200b...", html)
        self.assertIn("o_l10n_th_wht_cert_tawi", html)  # Sarabun font
        self.assertEqual(
            self._get_tawi_checked_boxes(html),
            ["(6) ภ.ง.ด.3ก", "(3) ออกให้ครั้งเดียว"],
        )
        # Description of other incomes (6) on its dotted line
        self.assertEqual(
            lxml_html.fromstring(html).xpath(
                "//span[contains(@class, 'position-relative')]"
                "/span[contains(@class, 'position-absolute')]/text()"
            ),
            ["Lottery"],
        )
        # Row 5: 1,000.00 and 30.00, row 6: 1,000.00 and 10.00, total 2,000.00
        for amount in ("1,000", "30", "10", "2,000", "40"):
            self.assertIn(f">{amount}<", html)
        # Total withholding in Thai words, ถ้วน once
        self.assertIn("สี่สิบบาทถ้วน", html)
        self.assertEqual(html.count("ถ้วน"), 1)
        self.assertEqual(cert_a._get_tawi_amount_text(3.12), "สามบาทสิบสองสตางค์")
        self.assertEqual(cert_a._get_tawi_amount_text(300.0), "สามร้อยบาทถ้วน")
        # A contact without address prints the address of its company
        self.assertIn("1 Sukhumvit Road", render(cert_b))

        # Print button of done certificates, bulk ZIP download from the list
        arch = self.env["withholding.tax.cert"].get_views([(False, "form")])["views"][
            "form"
        ]["arch"]
        for name in ("action_print_50_tawi", "action_send_by_email"):
            button = lxml_html.fromstring(arch).xpath(f"//button[@name='{name}']")[0]
            self.assertEqual(button.get("invisible"), "state != 'done'")
        action = cert_a.action_print_50_tawi()
        self.assertEqual(action["report_name"], "l10n_th_account_tax.report_wht_cert")
        self.assertEqual(action["context"]["active_ids"], cert_a.ids)
        bulk = self.env.ref("l10n_th_account_tax.action_download_50_tawi_zip")
        self.assertEqual(bulk.binding_model_id.model, "withholding.tax.cert")
        action = cert_a.action_download_50_tawi_bulk()
        self.assertEqual(action["type"], "ir.actions.act_url")
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "withholding.tax.cert"), ("res_id", "=", cert_a.id)]
        )
        self.assertEqual(len(attachment), 1)
        self.assertEqual(
            attachment.name, "WHT_{}.pdf".format(cert_a.number.replace("/", "-"))
        )
        self.assertTrue(action["url"].endswith(f"/{attachment.id}"))
        # Certificates not done are skipped with a warning
        action = certs.action_download_50_tawi_bulk()
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn(cert_b.display_name, action["params"]["message"])
        self.assertEqual(action["params"]["next"]["type"], "ir.actions.act_url")

        # Send by email
        action = cert_a.action_send_by_email()
        composer = (
            self.env["mail.compose.message"]
            .with_context(**action["context"])
            .create({})
        )
        self.assertEqual(
            composer.template_id,
            self.env.ref("l10n_th_account_tax.mail_template_wht_cert"),
        )
        self.assertIn(cert_a.number, composer.subject)
        self.assertEqual(composer.partner_ids, self.partner_a)
        composer.action_send_mail()
        message = cert_a.message_ids[0]
        self.assertEqual(message.partner_ids, self.partner_a)
        # The 50 Tawi, in HTML instead of PDF in tests
        self.assertTrue(
            message.attachment_ids.name.startswith(
                "WHT_{}.".format(cert_a.number.replace("/", "-"))
            )
        )

        # Standard 50 Tawi of payments are hidden
        arch = self.env["account.payment"].get_views([(False, "form")])["views"][
            "form"
        ]["arch"]
        buttons = lxml_html.fromstring(arch).xpath(
            "//button[@name='action_l10n_th_print_50_tawi']"
        )
        self.assertTrue(all(b.get("invisible") in ("1", "True") for b in buttons))
        self.assertFalse(
            self.env.ref("l10n_th.action_download_50_tawi_zip").binding_model_id
        )
