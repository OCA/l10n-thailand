# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from freezegun import freeze_time

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase
from odoo.tools import test_reports


@tagged("post_install", "-at_install")
class TestTHMultiCurrencyRevaluation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.move_model = cls.env["account.move"]
        cls.ml_model = cls.env["account.move.line"]
        cls.analytic_account_model = cls.env["account.analytic.account"]

        cls.currency_revaluation_wiz = cls.env["wizard.currency.revaluation"]
        cls.reverse_currency_revaluation_wiz = cls.env[
            "wizard.reverse.currency.revaluation"
        ]
        cls.revaluation_report = cls.env["unrealized.report.printer"]
        cls.type_expense = cls.env.ref("account.data_account_type_expenses")
        cls.type_receivable = cls.env.ref("account.data_account_type_receivable")
        cls.type_revenue = cls.env.ref("account.data_account_type_other_income")
        cls.partner = cls.env.ref("base.res_partner_4")
        cls.journal_general = cls.env["account.journal"].create(
            {"name": "Test General Journal", "code": "TGJ", "type": "general"}
        )
        cls.analytic_account = cls.analytic_account_model.create({"name": "test aa"})
        # Config multi currency revaluation in company
        cls.main_company = cls.env.ref("base.main_company")
        cls.main_company.write(
            {
                "currency_reval_journal_id": cls.journal_general.id,
            }
        )
        # Make sure that we're test with multi currency
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.usd_currency = cls.env.ref("base.USD")
        cls.eur_currency.active = True
        # Add currency rate
        cls.eur_currency.rate_ids.create(
            {
                "name": "2010-01-15",
                "company_rate": 0.1,
                "currency_id": cls.eur_currency.id,
            }
        )

        cls.account_exp = cls.account_model.create(
            {
                "code": "TEST-0001",
                "name": "Account-Test",
                "user_type_id": cls.type_expense.id,
            }
        )
        cls.account_rec = cls.account_model.create(
            {
                "code": "TEST-9999",
                "name": "Account-Test-Receive",
                "user_type_id": cls.type_receivable.id,
                "reconcile": True,
            }
        )
        cls.product = cls.env.ref("product.product_product_5")
        cls.account_rev = cls.account_model.create(
            {
                "code": "TEST-Gain",
                "name": "Account-Test-Gain",
                "user_type_id": cls.type_revenue.id,
            }
        )

    def create_invoice(self, amount, currency, bill=False):
        bill = self.move_model.create(
            {
                "move_type": "in_invoice" if bill else "out_invoice",
                "partner_id": self.partner.id,
                "currency_id": currency,
                "invoice_date": "2010-01-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                        },
                    )
                ],
            }
        )
        return bill

    def test_01_config_account(self):
        """Test that you change title"""
        account_revaluation = self.account_model.search(
            [("currency_revaluation", "=", True)]
        )
        self.assertTrue(account_revaluation)
        self.assertFalse(self.account_exp.currency_revaluation)
        # Do not allow revaluation with account not include_initial_balance
        with self.assertRaises(UserError):
            self.account_exp.write({"currency_revaluation": True})

        # Test select user_type_id is receivable, payable or Bank and Cash.
        # it should auto selected currency_revaluation field
        self.assertFalse(self.account_rec.currency_revaluation)
        with Form(self.account_rec) as acc:
            acc.user_type_id = self.type_receivable
        self.assertTrue(self.account_rec.currency_revaluation)

    @freeze_time("2010-01-05")
    def test_02_bill_multi_currency_revaluation(self):
        account_revaluation = self.account_model.search(
            [("currency_revaluation", "=", True)]
        )
        f = Form(self.currency_revaluation_wiz)
        wizard = f.save()
        self.assertEqual(wizard.journal_id, self.journal_general)
        self.assertEqual(wizard.revaluation_account_ids, account_revaluation)
        # Test not config loss/gain on company, it should error
        with self.assertRaises(UserError):
            wizard.revaluate_currency()
        self.main_company.write(
            {
                "revaluation_loss_account_id": self.account_exp.id,
                "revaluation_gain_account_id": self.account_rev.id,
            }
        )
        # Test no account in revaluation, not allow revalue
        with self.assertRaises(UserError):
            wizard.revaluation_account_ids = False
            wizard.revaluate_currency()
        # Test filter without date range, it will not found accounting entry
        with self.assertRaises(UserError):
            wizard.revaluate_currency()
        # Create bill
        bill = self.create_invoice(100, self.eur_currency, True)
        bill.action_post()
        self.assertEqual(bill.state, "posted")
        # Revalue
        wizard.revaluation_date = "2010-01-15"
        action = wizard.revaluate_currency()
        # Test revalue again, it should error
        with self.assertRaises(UserError):
            wizard.revaluate_currency()
        # Check link between original and revalue move
        ml = self.ml_model.browse(action["domain"][0][2])
        ml_revalue = ml.filtered("revaluation_origin_line_count")
        ml_origin = bill.line_ids.filtered("revaluation_created_line_id")
        self.assertEqual(ml_revalue.revaluation_origin_line_ids.move_id, bill)
        self.assertEqual(ml_origin.revaluation_created_line_id, ml_revalue)
        # Open link to original on ml
        action_view = ml_revalue.action_view_revaluation_origin_lines()
        self.assertTrue(action_view.get("views"))
        # No link it will return close
        action_view = ml.filtered(
            lambda l: not l.revaluation_origin_line_count
        ).action_view_revaluation_origin_lines()
        self.assertFalse(action_view.get("views"))
        # Open link to new revalue on ml
        action_view = ml_origin.action_view_revaluation_created_line()
        self.assertTrue(action_view.get("views"))
        # No link it will return close
        action_view = bill.line_ids.filtered(
            lambda l: not l.revaluation_created_line_id
        ).action_view_revaluation_created_line()
        self.assertFalse(action_view.get("views"))

        # Reverse revalue currency
        with Form(self.reverse_currency_revaluation_wiz) as f:
            f.revaluation_interval_start_date = "2010-01-01"
            f.revaluation_interval_end_date = "2010-01-17"
            f.reverse_posting_date = "2010-01-15"
        wizard = f.save()
        self.assertEqual(wizard.entries_to_reverse_ids, ml_revalue.move_id)
        action = wizard.reverse_revaluate_currency()
        self.ml_model.browse(action["domain"][0][2])

    def test_03_reverse_no_revalue(self):
        f = Form(self.reverse_currency_revaluation_wiz)
        wizard = f.save()
        # Test reverse revalue before revalue, it should error
        with self.assertRaises(UserError):
            wizard.reverse_revaluate_currency()

    @freeze_time("2010-01-05")
    def test_04_multi_currency_revaluation_report(self):
        # Create bill
        bill = self.create_invoice(100, self.eur_currency, True)
        bill.action_post()

        f = Form(self.currency_revaluation_wiz)
        wizard = f.save()
        # Revalue
        self.main_company.write(
            {
                "revaluation_loss_account_id": self.account_exp.id,
                "revaluation_gain_account_id": self.account_rev.id,
            }
        )
        wizard.revaluation_date = "2010-01-15"
        wizard.revaluate_currency()

        f = Form(self.revaluation_report)
        wizard = f.save()
        # Check date start must <= date end only
        with self.assertRaises(UserError):
            with Form(wizard) as wiz:
                wiz.start_date = "2020-01-01"
        # Cannot print report with not account
        with self.assertRaises(ValidationError):
            wizard.account_ids = False
            wizard.print_report()
        wizard.print_report()
        data = {
            "start_date": wizard.start_date,
            "end_date": "2020-01-31",
            "only_include_posted_entries": wizard.only_include_posted_entries,
            "account_ids": wizard.account_ids.ids,
        }
        result = test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "l10n_th_multicurrency_revaluation.curr_unrealized_report",
            wizard.ids,
            data=data,
        )
        self.assertTrue(result)

        # Test Export Excel
        # Cannot export excel report with not account
        with self.assertRaises(ValidationError):
            wizard.account_ids = False
            wizard.export_xlsx()
        wizard.export_xlsx()

        action = self.env.ref(
            "l10n_th_multicurrency_revaluation.action_report_currency_unrealized_xlsx"
        )
        action._render_xlsx(wizard.ids, data)

    @freeze_time("2010-01-05")
    def test_05_multi_currency_revaluation_invoice(self):
        # Create bill
        invoice = self.create_invoice(100, self.eur_currency)
        invoice.action_post()

        f = Form(self.currency_revaluation_wiz)
        wizard = f.save()
        # Revalue
        self.main_company.write(
            {
                "revaluation_loss_account_id": self.account_exp.id,
                "revaluation_gain_account_id": self.account_rev.id,
                "revaluation_analytic_account_id": self.analytic_account.id,
            }
        )
        wizard.revaluation_date = "2010-01-15"
        wizard.revaluate_currency()

    @freeze_time("2010-01-05")
    def test_06_company_currency_revaluation_invoice(self):
        # Create bill
        invoice = self.create_invoice(100, self.usd_currency)
        invoice.action_post()

        f = Form(self.currency_revaluation_wiz)
        wizard = f.save()
        # Revalue
        self.main_company.write(
            {
                "revaluation_loss_account_id": self.account_exp.id,
                "revaluation_gain_account_id": self.account_rev.id,
                "revaluation_analytic_account_id": self.analytic_account.id,
            }
        )
        wizard.revaluation_date = "2010-01-15"
        # Test company currency, it shouldn't revalue.
        with self.assertRaises(UserError):
            wizard.revaluate_currency()
