# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from .common import ThAccountTaxCommon


@tagged("post_install", "-at_install")
@freeze_time("2026-06-01")
class TestPersonalIncomeTax(ThAccountTaxCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pit_model = cls.env["personal.income.tax"]
        cls.default_pit = cls.env.ref("l10n_th_account_tax.thailand_pit")
        cls.default_pit_date = fields.Date.to_date("2026-06-01")
        cls.pit_table = cls._create_pit_rate_table("2099")
        cls.payment_date = fields.Date.to_date("2099-10-05")
        # The PIT is withheld without the withholding tax base account
        cls.company.withholding_tax_base_account_id = False
        cls.pit_tax = cls._create_wht_tax(
            "PIT - Personal Income Tax Test", amount=0.0, is_pit=True
        )
        cls.wht_tax = cls._create_wht_tax(
            "WHT 3% - Personal Income Tax Test", amount=-3.0
        )

    def _create_payment_register(self, moves, **values):
        values.setdefault("payment_date", self.payment_date)
        return super()._create_payment_register(moves, **values)

    def _pit_tax_vals(self, name, **kwargs):
        return {
            "name": name,
            "amount_type": "percent",
            "amount": 0.0,
            "type_tax_use": "purchase",
            "is_withholding_tax": True,
            "is_pit": True,
            **kwargs,
        }

    @classmethod
    def _create_pit_rate_table(cls, calendar_year, rate_ranges=None):
        rate_ranges = rate_ranges or [
            (0.0, 150000.0, 0.0),
            (150000.0, 300000.0, 5.0),
            (300000.0, 500000.0, 10.0),
            (500000.0, 99999999999.0, 15.0),
        ]
        with Form(cls.env["personal.income.tax"]) as pit_form:
            pit_form.calendar_year = calendar_year
            for income_from, income_to, tax_rate in rate_ranges:
                with pit_form.rate_ids.new() as rate:
                    rate.income_from = income_from
                    rate.income_to = income_to
                    rate.tax_rate = tax_rate
        return pit_form.save()

    def _create_individual(self, name):
        """Another individual, with its own yearly income"""
        return self.env["res.partner"].create(
            {
                "name": name,
                "is_company": False,
                "country_id": self.env.ref("base.th").id,
            }
        )

    def _create_pit_entry(
        self, amount, entry_date="2099-01-01", partner=None, tax=None
    ):
        return self._create_tax_entry(
            tax or self.pit_tax,
            [(partner or self.partner_a, amount)],
            date=entry_date,
        )

    def _create_bill(
        self, lines, currency=None, invoice_date="2099-10-01", partner=None
    ):
        return self._create_th_invoice(
            "in_invoice",
            lines,
            partner=partner,
            date=invoice_date,
            currency=currency,
            post=True,
        )

    def _create_prior_income(self, amount, partner=None):
        entry = self._create_pit_entry(amount, partner=partner)
        entry.action_post()
        self._assert_yearly_income(amount, partner=partner)
        return entry

    def _new_pit_tax_form(self, name):
        with Form(self.env["account.tax"]) as tax_form:
            tax_form.name = name
            tax_form.type_tax_use = "purchase"
            tax_form.amount_type = "fixed"
            tax_form.amount = 3.0
            tax_form.is_withholding_tax = True
            tax_form.l10n_th_income_tax_type = "commission"
            self.assertFalse(tax_form._get_modifier("amount_type", "invisible"))
            self.assertFalse(tax_form._get_modifier("amount", "invisible"))
            tax_form.is_pit = True
            self.assertTrue(tax_form._get_modifier("amount_type", "invisible"))
            self.assertTrue(tax_form._get_modifier("amount", "invisible"))
            self.assertEqual(tax_form.amount_type, "percent")
            self.assertEqual(tax_form.amount, 0.0)
        return tax_form.record

    def _assert_yearly_income(self, amount, pit_date=None, partner=None):
        pit_date = pit_date or self.payment_date
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner or self.partner_a, pit_date),
            amount,
        )

    def _create_and_check_pit_cert(self, payment, base, amount, percent):
        self.assertTrue(payment.has_wht)
        self.assertEqual(payment.wht_cert_status, "none")
        payment.action_create_wht_cert()
        self.assertRecordValues(
            payment.wht_cert_ids.wht_line,
            [
                {
                    "wht_tax_id": self.pit_tax.id,
                    "base": base,
                    "amount": amount,
                    "wht_percent": percent,
                }
            ],
        )

    def test_00_pit_tax(self):
        """PIT is a 0% purchase withholding tax, one per company, its rate is
        hidden on the tax form."""
        with Form(self.pit_tax) as tax_form:
            tax_form.is_pit = False
            tax_form.amount_type = "fixed"
            tax_form.amount = 3.0
            tax_form.is_withholding_tax = True
            tax_form.l10n_th_income_tax_type = "commission"
            self.assertFalse(tax_form._get_modifier("amount", "invisible"))
            tax_form.is_pit = True
            self.assertTrue(tax_form._get_modifier("amount_type", "invisible"))
            self.assertTrue(tax_form._get_modifier("amount", "invisible"))
        self.assertRecordValues(
            tax_form.record,
            [
                {
                    "is_pit": True,
                    "amount_type": "percent",
                    "amount": 0.0,
                    "is_withholding_tax": True,
                }
            ],
        )

        tax_model = self.env["account.tax"]
        with self.assertRaisesRegex(ValidationError, "purchase withholding tax"):
            tax_model.create(
                self._pit_tax_vals(
                    "PIT Constraint Test - Not Withholding",
                    is_withholding_tax=False,
                )
            )
        with self.assertRaisesRegex(ValidationError, "purchase withholding tax"):
            tax_model.create(
                self._pit_tax_vals(
                    "PIT Constraint Test - Sales Tax",
                    type_tax_use="sale",
                )
            )
        with self.assertRaisesRegex(ValidationError, "percentage tax of 0%"):
            tax_model.create(
                self._pit_tax_vals("PIT Constraint Test - Nonzero", amount=-5.0)
            )
        with self.assertRaisesRegex(ValidationError, "Only one personal income tax"):
            tax_model.create(self._pit_tax_vals("PIT Constraint Test - Duplicate"))

        company_2 = self.setup_other_company()["company"]
        other_company_pit = tax_model.with_company(company_2).create(
            self._pit_tax_vals(
                "PIT Constraint Test - Other Company",
                company_id=company_2.id,
            )
        )
        self.assertEqual(other_company_pit.company_id, company_2)

        # A new tax set as PIT, once the PIT of the company is archived
        with self.assertRaisesRegex(ValidationError, "Only one personal income tax"):
            self._new_pit_tax_form("PIT Form Test - Duplicate")

        self.pit_tax.active = False
        new_pit = self._new_pit_tax_form("PIT Form Test - From Scratch")
        self.assertRecordValues(
            new_pit,
            [
                {
                    "is_pit": True,
                    "is_withholding_tax": True,
                    "type_tax_use": "purchase",
                    "amount_type": "percent",
                    "amount": 0.0,
                    "company_id": self.env.company.id,
                }
            ],
        )
        self.assertNotEqual(new_pit, self.pit_tax)

    def test_01_pit_rate(self):
        """Progressive PIT rate tables, without gaps, the latest active table
        effective on the payment date is used."""
        self.assertEqual(self.pit_table.calendar_year, "2099")
        self.assertEqual(
            self.pit_table.effective_date, fields.Date.to_date("2099-01-01")
        )
        self.assertRecordValues(
            self.pit_table.rate_ids,
            [
                {"income_from": 0.0, "income_to": 150000.0, "tax_rate": 0.0},
                {
                    "income_from": 150000.0,
                    "income_to": 300000.0,
                    "tax_rate": 5.0,
                },
                {
                    "income_from": 300000.0,
                    "income_to": 500000.0,
                    "tax_rate": 10.0,
                },
                {
                    "income_from": 500000.0,
                    "income_to": 99999999999.0,
                    "tax_rate": 15.0,
                },
            ],
        )

        rates = self.default_pit.rate_ids
        self.assertEqual(rates[0].income_from, 0.0)
        self.assertEqual(rates[0].tax_rate, 0.0)
        self.assertEqual(rates[1].income_from, 150000.0)
        self.assertEqual(rates[1].tax_rate, 5.0)

        self.assertEqual(
            self.default_pit.calculate_rate_wht(
                200000.0, 200000.0, self.default_pit_date
            ),
            2500.0,
        )
        self.assertEqual(
            self.default_pit.calculate_rate_wht(
                200000.0, 100000.0, self.default_pit_date
            ),
            2500.0,
        )
        self.assertEqual(
            self.default_pit.calculate_rate_wht(
                400000.0, 200000.0, self.default_pit_date
            ),
            15000.0,
        )
        self.assertEqual(
            self.default_pit.calculate_rate_wht(
                100000.0, 100000.0, self.default_pit_date
            ),
            0.0,
        )

        with self.assertRaises(UserError):
            self.pit_model.create(
                {
                    "calendar_year": "2199",
                    "rate_ids": [
                        Command.create(
                            {
                                "income_from": 0.0,
                                "income_to": 100.0,
                                "tax_rate": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                "income_from": 200.0,
                                "income_to": 300.0,
                                "tax_rate": 5.0,
                            }
                        ),
                    ],
                }
            )

        # A payment before the first effective PIT table reports a clear error
        default_pit = self.env.ref("l10n_th_account_tax.thailand_pit")
        self.assertEqual(default_pit.effective_date, fields.Date.to_date("2017-01-01"))
        bill = self._create_bill([(100000.0, self.pit_tax, self.expense_account)])
        with self.assertRaisesRegex(UserError, "No effective PIT rate table"):
            wizard = self._create_payment_register(bill, payment_date="2016-12-31")
            self._pay(bill, wizard=wizard)

        table_2098 = self._create_pit_rate_table(
            "2098",
            rate_ranges=[
                (0.0, 100000.0, 0.0),
                (100000.0, 99999999999.0, 10.0),
            ],
        )
        expected_tables = (
            ("2100-06-30", self.pit_table),
            ("2099-10-05", self.pit_table),
            ("2099-01-01", self.pit_table),
            ("2098-12-31", table_2098),
            ("2098-01-01", table_2098),
            ("2097-12-31", self.default_pit),
        )
        for pit_date, expected in expected_tables:
            self.assertEqual(
                self.pit_model._get_effective_pit(fields.Date.to_date(pit_date)),
                expected,
                pit_date,
            )

        # A payment of 2098 is taxed with the 2098 table (10% above 100,000)
        pay_date = fields.Date.to_date("2098-06-01")
        bill_1 = self._create_bill(
            [(150000.0, self.pit_tax, self.expense_account)],
            invoice_date="2098-06-01",
        )
        wizard_1 = self._create_payment_register(bill_1, payment_date=pay_date)
        self._assert_withholding_lines(wizard_1, [(self.pit_tax, 150000.0, 5000.0)])
        self.assertEqual(wizard_1.withholding_net_amount, 145000.0)
        self._pay(bill_1, wizard=wizard_1)
        self._assert_yearly_income(150000.0, pay_date)

        # Archived tables are ignored, the previous active table applies
        table_2098.active = False
        self.assertEqual(
            self.pit_model._get_effective_pit(fields.Date.to_date("2098-12-31")),
            self.default_pit,
        )
        self.assertEqual(
            self.pit_model._get_effective_pit(fields.Date.to_date("2099-10-05")),
            self.pit_table,
        )
        pay_date_2 = fields.Date.to_date("2098-07-01")
        bill_2 = self._create_bill(
            [(100000.0, self.pit_tax, self.expense_account)],
            invoice_date="2098-07-01",
        )
        # Default table, 5% from 150,000: 250,000 of yearly income, 100,000 paid
        wizard_2 = self._create_payment_register(bill_2, payment_date=pay_date_2)
        self._assert_withholding_lines(wizard_2, [(self.pit_tax, 100000.0, 5000.0)])
        self._pay(bill_2, wizard=wizard_2)
        self._assert_yearly_income(250000.0, pay_date_2)

        # Without any active table effective on the date, there is no PIT rate
        self.pit_table.active = False
        self.default_pit.active = False
        with self.assertRaisesRegex(UserError, "No effective PIT rate table"):
            self.pit_model._get_effective_pit(fields.Date.to_date("2099-10-05"))

    def test_02_withholding_tax_pit(self):
        """Accumulate the yearly income of an individual through bills, payments,
        certificates and report. PIT income is shown for individuals only."""
        company_contact = self.env["res.partner"].create(
            {"name": "Company Contact", "parent_id": self.partner_b.id}
        )
        self.assertTrue(self.partner_a.show_pit_income)
        self.assertFalse(self.partner_b.show_pit_income)
        self.assertFalse(company_contact.show_pit_income)

        self.company.withholding_tax_base_account_id = self.wht_base_account

        bill_1 = self._create_bill(
            [(100000.0, self.pit_tax, self.expense_account)],
            invoice_date="2099-01-15",
        )
        date_1 = fields.Date.to_date("2099-01-15")
        self._assert_yearly_income(0.0, date_1)
        wizard_1 = self._create_payment_register(bill_1, payment_date=date_1)
        self.assertEqual(wizard_1.withhold, "withhold_pay")
        self.assertEqual(bill_1.withholding_residual_amount_currency, 0.0)
        self._assert_withholding_lines(wizard_1, [(self.pit_tax, 100000.0, 0.0)])
        self.assertEqual(wizard_1.withholding_net_amount, 100000.0)
        payment_1 = self._pay(bill_1, wizard=wizard_1)
        self.assertEqual(payment_1.withholding_net_amount, 100000.0)
        self._assert_yearly_income(100000.0, date_1)
        self.assertRecordValues(
            bill_1,
            [
                {
                    "withholding_residual_amount_currency": 0.0,
                    "payment_state": "paid",
                }
            ],
        )
        base_line = payment_1.move_id.line_ids.filtered(
            lambda line: self.pit_tax in line.tax_ids
        )
        self.assertRecordValues(
            base_line,
            [
                {
                    "name": "WH Base Counterpart",
                    "partner_id": self.partner_a.id,
                    "balance": 100000.0,
                    "tax_repartition_line_id": False,
                }
            ],
        )
        self._create_and_check_pit_cert(payment_1, 100000.0, 0.0, 0.0)

        bill_2 = self._create_bill(
            [(100000.0, self.pit_tax, self.expense_account)],
            invoice_date="2099-04-15",
        )
        date_2 = fields.Date.to_date("2099-04-15")
        self._assert_yearly_income(100000.0, date_2)
        wizard_2 = self._create_payment_register(bill_2, payment_date=date_2)
        self.assertEqual(wizard_2.withhold, "withhold_pay")
        self.assertEqual(bill_2.withholding_residual_amount_currency, 0.0)
        self._assert_withholding_lines(wizard_2, [(self.pit_tax, 100000.0, 2500.0)])
        self.assertEqual(wizard_2.withholding_net_amount, 97500.0)
        payment_2 = self._pay(bill_2, wizard=wizard_2)
        self.assertEqual(payment_2.withholding_net_amount, 97500.0)
        self._assert_yearly_income(200000.0, date_2)
        self.assertEqual(bill_2.payment_state, "paid")
        self.assertEqual(bill_2.withholding_residual_amount_currency, 0.0)
        self._create_and_check_pit_cert(payment_2, 100000.0, 2500.0, 2.5)

        bill_3 = self._create_bill(
            [(200000.0, self.pit_tax, self.expense_account)],
            invoice_date="2099-10-05",
        )
        date_3 = fields.Date.to_date("2099-10-05")
        self._assert_yearly_income(200000.0, date_3)
        wizard_3 = self._create_payment_register(bill_3, payment_date=date_3)
        self.assertEqual(wizard_3.withhold, "withhold_pay")
        self.assertEqual(bill_3.withholding_residual_amount_currency, 0.0)
        self._assert_withholding_lines(wizard_3, [(self.pit_tax, 200000.0, 15000.0)])
        self.assertEqual(wizard_3.withholding_net_amount, 185000.0)
        payment_3 = self._pay(bill_3, wizard=wizard_3)
        self.assertEqual(payment_3.withholding_net_amount, 185000.0)
        self._assert_yearly_income(400000.0, date_3)
        self.assertEqual(bill_3.payment_state, "paid")
        self.assertEqual(bill_3.withholding_residual_amount_currency, 0.0)
        self._create_and_check_pit_cert(payment_3, 200000.0, 15000.0, 7.5)

        payments = payment_1 | payment_2 | payment_3
        self.partner_a.invalidate_recordset(["wht_cert_count"])
        self.assertEqual(self.partner_a.wht_cert_count, 3)
        self.assertEqual(
            self.partner_a.button_wht_certs()["domain"],
            [("partner_id", "=", self.partner_a.id)],
        )

        action = self.partner_a.action_view_pit_income()
        self.assertEqual(action["res_model"], "wht.report")
        self.assertEqual(
            action["domain"],
            [
                ("partner_id", "=", self.partner_a.id),
                ("is_pit", "=", True),
            ],
        )
        report = self.env["wht.report"]
        rows = report.search(action["domain"])
        self.assertEqual(sum(rows.mapped("amount_income")), 400000.0)
        self.assertEqual(sum(rows.mapped("amount_wht")), 17500.0)
        self.assertSetEqual(set(rows.payment_id.ids), set(payments.ids))
        for row in rows:
            self.assertIn(row.payment_id, payments)
            self.assertEqual(row.tax_id, self.pit_tax)
            self.assertEqual(row.calendar_year, "2099")
        self.assertEqual(
            report._read_group(
                action["domain"],
                groupby=["calendar_year"],
                aggregates=["amount_income:sum", "amount_wht:sum"],
            ),
            [("2099", 400000.0, 17500.0)],
        )

    def test_03_withholding_tax_pit_payments(self):
        """Payments of bills with PIT: partial, with other withholding tax, in
        foreign currency, direct, with split or edited PIT lines, in a group tax."""
        # Partial bill payments
        partner = self._create_individual("Partial bill payments")
        bill = self._create_bill(
            [(200000.0, self.pit_tax, self.expense_account)], partner=partner
        )
        first = self._create_payment_register(bill, amount=100000.0)
        self._assert_withholding_lines(first, [(self.pit_tax, 100000.0, 0.0)])
        self._pay(bill, wizard=first)
        self._assert_yearly_income(100000.0, partner=partner)
        self.assertEqual(bill.amount_residual, 100000.0)

        second = self._create_payment_register(bill)
        self._assert_withholding_lines(second, [(self.pit_tax, 100000.0, 2500.0)])
        self._pay(bill, wizard=second)
        self._assert_yearly_income(200000.0, partner=partner)
        self.assertEqual(bill.payment_state, "paid")

        # PIT and withholding tax
        partner = self._create_individual("PIT and withholding tax")
        self._create_prior_income(200000.0, partner=partner)
        bill = self._create_bill(
            [
                (100000.0, self.pit_tax, self.expense_account),
                (1000.0, self.wht_tax, self.expense_account),
            ],
            partner=partner,
        )
        wizard = self._create_payment_register(bill)
        self._assert_withholding_lines(
            wizard,
            [(self.pit_tax, 100000.0, 5000.0), (self.wht_tax, 1000.0, 30.0)],
        )
        self._pay(bill, wizard=wizard)
        self.assertEqual(bill.withholding_residual_amount_currency, 0.0)
        self.assertEqual(bill.payment_state, "paid")
        self._assert_yearly_income(300000.0, partner=partner)

        # Partial payment residual
        partner = self._create_individual("Partial payment residual")
        self._create_prior_income(200000.0, partner=partner)
        bill = self._create_bill(
            [
                (100000.0, self.pit_tax, self.expense_account),
                (1000.0, self.wht_tax, self.expense_account),
            ],
            partner=partner,
        )
        wizard = self._create_payment_register(bill, amount=bill.amount_total / 2)
        self._assert_withholding_lines(
            wizard,
            [(self.pit_tax, 50000.0, 2500.0), (self.wht_tax, 500.0, 15.0)],
        )
        self._pay(bill, wizard=wizard)
        self.assertEqual(bill.withholding_residual_amount_currency, 15.0)
        self.assertEqual(bill.payment_state, "partial")
        self._assert_yearly_income(250000.0, partner=partner)

        # Foreign currency payment
        partner = self._create_individual("Foreign currency payment")
        eur = self.setup_other_currency("EUR", rates=[("2099-01-01", 2.0)])
        self._create_prior_income(100000.0, partner=partner)
        bill = self._create_bill(
            [(200000.0, self.pit_tax, self.expense_account)],
            currency=eur,
            partner=partner,
        )
        wizard = self._create_payment_register(bill, currency_id=eur.id)
        self.assertEqual(wizard.currency_id, eur)
        self._assert_withholding_lines(wizard, [(self.pit_tax, 200000.0, 5000.0)])
        payment = self._pay(bill, wizard=wizard)
        self.assertEqual(payment.currency_id, eur)
        self.assertEqual(payment.withholding_net_amount, 195000.0)
        self._assert_yearly_income(200000.0, partner=partner)

        # Direct payment
        partner = self._create_individual("Direct payment")
        self._create_prior_income(100000.0, partner=partner)
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "partner_id": partner.id,
                "amount": 100000.0,
                "date": self.payment_date,
                "currency_id": self.env.company.currency_id.id,
                "journal_id": self.bank_journal.id,
                "payment_method_line_id": self.outbound_payment_method_line.id,
                "withhold": "withhold_pay",
                "withholding_line_ids": [
                    Command.create(
                        {
                            "tax_id": self.pit_tax.id,
                            "account_id": self.expense_account.id,
                            "base_amount": 100000.0,
                        }
                    )
                ],
            }
        )
        self._assert_withholding_lines(payment, [(self.pit_tax, 100000.0, 2500.0)])
        self.assertEqual(payment.withholding_net_amount, 97500.0)
        payment.action_post()
        self.assertEqual(payment.move_id.state, "posted")
        self._assert_yearly_income(200000.0, partner=partner)

        # Split PIT lines
        partner = self._create_individual("Split PIT lines")
        self._create_prior_income(140000.0, partner=partner)
        other_expense = self._create_account(
            "PIT Test Other Service Expense", "PITEXP", "expense"
        )
        self.assertFalse(self.env.company.withholding_tax_base_account_id)
        bill = self._create_bill(
            [
                (5000.0, self.pit_tax, self.expense_account),
                (15000.0, self.pit_tax, other_expense),
            ],
            partner=partner,
        )
        wizard = self._create_payment_register(bill)
        lines = wizard.withholding_line_ids
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines.tax_id, self.pit_tax)
        self.assertCountEqual(
            lines.account_id.ids, (self.expense_account | other_expense).ids
        )
        self.assertEqual(sorted(lines.mapped("base_amount")), [5000.0, 15000.0])
        self.assertEqual(sum(lines.mapped("amount")), 500.0)
        payment = self._pay(bill, wizard=wizard)
        self.assertEqual(sum(payment.withholding_line_ids.mapped("amount")), 500.0)
        self._assert_yearly_income(160000.0, partner=partner)

        # Edited PIT base
        partner = self._create_individual("Edited PIT base")
        self._create_prior_income(140000.0, partner=partner)
        bill = self._create_bill(
            [
                (5000.0, self.pit_tax, self.expense_account),
                (15000.0, self.pit_tax, other_expense),
            ],
            partner=partner,
        )
        wizard = self._create_payment_register(bill)
        lines = wizard.withholding_line_ids
        self.assertEqual(len(lines), 2)
        self.assertEqual(sum(lines.mapped("amount")), 500.0)
        first_line = lines.filtered(lambda line: line.base_amount == 5000.0)
        second_line = lines - first_line
        second_amount = second_line.amount

        # (140,000 + 20,000 + 15,000 - 150,000 exempted) * 5%
        first_line.base_amount = 20000.0
        self.assertNotEqual(second_line.amount, second_amount)
        self.assertEqual(sum(lines.mapped("amount")), 1250.0)

        payment = self._pay(bill, wizard=wizard)
        self.assertEqual(sum(payment.withholding_line_ids.mapped("amount")), 1250.0)
        self._assert_yearly_income(175000.0, partner=partner)

        # PIT in a group tax
        partner = self._create_individual("PIT in a group tax")
        group_tax = self.env["account.tax"].create(
            {
                "name": "PIT Group Tax Test",
                "amount_type": "group",
                "type_tax_use": "purchase",
                "children_tax_ids": [Command.set(self.pit_tax.ids)],
            }
        )
        self._create_prior_income(100000.0, partner=partner)
        bill = self._create_bill(
            [(100000.0, group_tax, self.expense_account)], partner=partner
        )
        wizard = self._create_payment_register(bill)
        self.assertEqual(wizard.withhold, "withhold_pay")
        # (100,000 + 100,000 - 150,000 exempted) * 5%
        self._assert_withholding_lines(wizard, [(self.pit_tax, 100000.0, 2500.0)])
        payment = self._pay(bill, wizard=wizard)
        self.assertEqual(payment.withholding_net_amount, 97500.0)
        self.assertEqual(bill.payment_state, "paid")
        self._assert_yearly_income(200000.0, partner=partner)

    def test_04_pit_get_model_move(self):
        """Yearly income from posted PIT journal entries of the partner and year:
        reset, reversal, negative income, and the PIT report."""
        # Posted entries of the year
        partner = self._create_individual("Posted entries of the year")
        first = self._create_pit_entry(
            10000.0, entry_date="2026-01-01", partner=partner
        )
        first.action_post()
        second = self._create_pit_entry(
            15000.0, entry_date="2026-12-31", partner=partner
        )
        second.action_post()
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner, self.default_pit_date),
            25000.0,
        )

        previous_year = self._create_pit_entry(
            7000.0, entry_date="2025-12-31", partner=partner
        )
        previous_year.action_post()
        draft = self._create_pit_entry(3000.0, entry_date="2026-01-01", partner=partner)
        self.assertEqual(draft.state, "draft")
        other_partner = self._create_pit_entry(
            5000.0, entry_date="2026-01-01", partner=self.partner_b
        )
        other_partner.action_post()
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner, self.default_pit_date),
            25000.0,
        )
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(
                partner, fields.Date.to_date("2025-06-01")
            ),
            7000.0,
        )

        # Reset and reversal
        partner = self._create_individual("Reset and reversal")
        move = self._create_pit_entry(10000.0, entry_date="2026-01-01", partner=partner)
        move.action_post()
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner, self.default_pit_date),
            10000.0,
        )
        move.button_draft()
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner, self.default_pit_date),
            0.0,
        )
        move.action_post()
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner, self.default_pit_date),
            10000.0,
        )
        reversal = move._reverse_moves(cancel=True)
        self.assertEqual(reversal.state, "posted")
        self.assertEqual(reversal.date.year, self.default_pit_date.year)
        self.assertEqual(
            self.pit_model._get_pit_amount_yearly(partner, self.default_pit_date),
            0.0,
        )

        # Negative yearly income
        partner = self._create_individual("Negative yearly income")
        previous = self._create_pit_entry(
            80000.0, entry_date="2098-12-31", partner=partner
        )
        previous.action_post()
        self._assert_yearly_income(
            80000.0, fields.Date.to_date("2098-12-31"), partner=partner
        )
        # Reversed in the next year, which starts with a negative income
        reversal = previous._reverse_moves(
            [{"date": fields.Date.to_date("2099-01-10")}], cancel=True
        )
        self.assertEqual(reversal.state, "posted")
        self._assert_yearly_income(-80000.0, partner=partner)
        self._assert_yearly_income(
            80000.0, fields.Date.to_date("2098-12-31"), partner=partner
        )

        # (300,000 - 80,000 - 150,000 exempted) * 5%
        bill = self._create_bill(
            [(300000.0, self.pit_tax, self.expense_account)], partner=partner
        )
        wizard = self._create_payment_register(bill)
        self.assertEqual(wizard.withhold, "withhold_pay")
        self._assert_withholding_lines(wizard, [(self.pit_tax, 300000.0, 3500.0)])
        self.assertEqual(wizard.withholding_net_amount, 296500.0)
        payment = self._pay(bill, wizard=wizard)
        self.assertEqual(payment.withholding_net_amount, 296500.0)
        self.assertEqual(bill.payment_state, "paid")
        self.assertEqual(bill.withholding_residual_amount_currency, 0.0)
        self._assert_yearly_income(220000.0, partner=partner)

        # Negative after payment
        partner = self._create_individual("Negative after payment")
        previous = self._create_pit_entry(
            300000.0, entry_date="2098-12-31", partner=partner
        )
        previous.action_post()
        previous._reverse_moves(
            [{"date": fields.Date.to_date("2099-01-10")}], cancel=True
        )
        self._assert_yearly_income(-300000.0, partner=partner)

        bill = self._create_bill(
            [(100000.0, self.pit_tax, self.expense_account)], partner=partner
        )
        wizard = self._create_payment_register(bill)
        self._assert_withholding_lines(wizard, [(self.pit_tax, 100000.0, 0.0)])
        self.assertEqual(wizard.withholding_net_amount, 100000.0)
        self._pay(bill, wizard=wizard)
        self.assertEqual(bill.payment_state, "paid")
        self._assert_yearly_income(-200000.0, partner=partner)

        # PIT report
        partner = self._create_individual("PIT report")
        wht_bill = self._create_bill(
            [(1000.0, self.wht_tax, self.expense_account)], partner=partner
        )
        self._pay(wht_bill)
        draft = self._create_prior_income(3000.0, partner=partner)
        draft.button_draft()
        self.assertEqual(draft.state, "draft")
        self._create_bill(
            [(100000.0, self.pit_tax, self.expense_account)], partner=partner
        )
        other_entry = draft.copy()
        other_entry.line_ids.write({"partner_id": self.partner_b.id})
        other_entry.action_post()

        report = self.env["wht.report"]
        domain = [
            ("partner_id", "=", partner.id),
            ("is_pit", "=", True),
        ]
        self.assertTrue(report.search([("move_id", "=", other_entry.id)]))
        self.assertFalse(report.search(domain))

        bill = self._create_bill(
            [(100000.0, self.pit_tax, self.expense_account)], partner=partner
        )
        payment = self._pay(bill)
        rows = report.search(domain)
        self.assertTrue(rows)
        self.assertEqual(rows.move_id, payment.move_id)
        payment.move_id.button_draft()
        self.assertEqual(payment.move_id.state, "draft")
        self.assertFalse(report.search(domain))
