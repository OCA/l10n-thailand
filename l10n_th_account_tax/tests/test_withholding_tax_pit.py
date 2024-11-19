# Copyright 2021 Ecosoft Co., Ltd. <http://ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestWithholdingTaxPIT(AccountTestInvoicingCommon):
    @classmethod
    @freeze_time("2001-02-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.account_wht_obj = cls.env["account.withholding.tax"]
        cls.partner_obj = cls.env["res.partner"]
        cls.product_obj = cls.env["product.product"]
        cls.wiz_payment_register_obj = cls.env["account.payment.register"]
        cls.account_account_obj = cls.env["account.account"]
        cls.account_payment_obj = cls.env["account.payment"]
        cls.journal_obj = cls.env["account.journal"]

        cls.partner = cls.partner_obj.create({"name": "Test Partner"})
        cls.product = cls.product_obj.create({"name": "Test", "standard_price": 500.0})
        cls.journal_bank = cls.company_data["default_journal_bank"]
        cls.purchase_journal = cls.company_data["default_journal_purchase"]
        cls.expense_account = cls.company_data["default_account_expense"]

        # Setup PIT withholding tax
        cls.account_pit = cls.account_account_obj.create(
            {
                "code": "100",
                "name": "Personal Income Tax",
                "account_type": "asset_current",
                "wht_account": True,
            }
        )
        cls.wht_pit = cls.account_wht_obj.create(
            {
                "name": "PIT",
                "account_id": cls.account_pit.id,
                "is_pit": True,
            }
        )
        cls.wht_1 = cls.account_wht_obj.create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.account_pit.id,
                "amount": 1,
            }
        )

    def _create_pit(self, calendar_year):
        """Create a simple PIT rate table"""
        with Form(self.env["personal.income.tax"]) as f:
            f.calendar_year = calendar_year
            with f.rate_ids.new() as rate:
                rate.income_from = 0
                rate.income_to = 1000
                rate.tax_rate = 0
            with f.rate_ids.new() as rate:
                rate.income_from = 1000
                rate.income_to = 2000
                rate.tax_rate = 2
            with f.rate_ids.new() as rate:
                rate.income_from = 2000
                rate.income_to = 9999999999999
                rate.tax_rate = 4
        return f.save()

    @freeze_time("2001-02-01")
    def _create_invoice(self, data):
        """Create test invoice
        data = [{
            "product_id": <value>,
            "quantity": <value>,
            "account_id": <value>,
            "name": <value>,
            "price_unit": <value>,
            "wht_tax_id": <value>,
        }, ...]
        """
        invoice_dict = {
            "name": "/",
            "partner_id": self.partner.id,
            "journal_id": self.purchase_journal.id,
            "move_type": "in_invoice",
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": line.get("product_id", self.product.id),
                        "quantity": line.get("quantity", 1.0),
                        "account_id": line.get("account_id", self.expense_account.id),
                        "name": line.get("name", "Advice"),
                        "price_unit": line.get("price_unit", 0.0),
                        "wht_tax_id": line.get("wht_tax_id", False),
                        "tax_ids": False,  # Clear all taxes
                    },
                )
                for line in data
            ],
        }
        invoice = self.env["account.move"].create(invoice_dict)
        return invoice

    def test_00_pit_tax(self):
        """No 2 PIT Tax allowed"""
        with self.assertRaises(ValidationError):
            self.wht_pit = self.account_wht_obj.create(
                {
                    "name": "PIT2",
                    "account_id": self.account_pit.id,
                    "is_pit": True,
                }
            )

    @freeze_time("2001-02-01")
    def test_01_pit_rate(self):
        """Test PIT Rate table"""
        # Create an effective PIT Rate
        self.pit_rate = self._create_pit("2001")
        # Test effective date
        self.assertEqual(self.pit_rate.calendar_year, "2001")
        self.assertEqual(self.pit_rate.effective_date, datetime.date(2001, 1, 1))
        # First rate must be zero
        with self.assertRaises(UserError):
            with Form(self.pit_rate) as pit_rate:
                with pit_rate.rate_ids.edit(0) as rate:
                    rate.income_from = 1
        # income_to must equal previous income_from
        with self.assertRaises(UserError):
            with Form(self.pit_rate) as pit_rate:
                with pit_rate.rate_ids.edit(1) as rate:
                    rate.income_from = 1001
        # Copy PIT, it will add copy after calendar year
        # User MUST change to to calendar year
        pit_rate_copy = self.pit_rate.copy()
        self.assertEqual(
            pit_rate_copy.calendar_year, f"{self.pit_rate.calendar_year} (copy)"
        )
        self.assertFalse(pit_rate_copy.effective_date)

    @freeze_time("2001-02-01")
    def test_02_withholding_tax_pit(self):
        """Create 3 Invoice/Payment, and check validity of amount
        Based on pit_rate table,
        - 1st invoice = 500, withhold = 0
        - 2nd invoice = 1000, withhold = 500*0.02 = 10
        - 3nd invoice = 1000, withhold = 500*0.02 + 500*0.04 = 30
        Then, create withholding tax cert for year 2001, total withholding = 40
        """
        # 1st invoice
        data = [
            {
                "price_unit": 500.0,
                "wht_tax_id": self.wht_pit.id,
            },
            {
                "price_unit": 1500.0,
                "wht_tax_id": False,
            },
        ]
        invoice1 = self._create_invoice(data)
        invoice1.action_post()

        # Register payment, without PIT rate yet
        with self.assertRaisesRegex(UserError, r"No effective PIT rate for date"):
            Form.from_action(self.env, invoice1.action_register_payment())

        # Create an effective PIT Rate, and try again.
        self.pit_rate = self._create_pit("2001")

        with Form.from_action(self.env, invoice1.action_register_payment()) as wiz_form:
            self.assertEqual(wiz_form.amount, 2000)
            self.assertEqual(wiz_form.payment_difference_handling, "open")
            wiz_form.save().action_create_payments()

        # PIT created but not PIT amount yet.
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_income")), 500)
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_wht")), 0)

        # 2nd invoice
        data = [
            {
                "price_unit": 1000.0,
                "wht_tax_id": self.wht_pit.id,
            }
        ]
        invoice2 = self._create_invoice(data)
        invoice2.action_post()

        with Form.from_action(self.env, invoice2.action_register_payment()) as wiz_form:
            self.assertEqual(wiz_form.amount, 990.0)
            self.assertEqual(wiz_form.payment_difference_handling, "reconcile")
            self.assertEqual(wiz_form.payment_difference, 10.0)
            wiz_form.save().action_create_payments()

        # Sum up amount_income and withholding amount = 10
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_income")), 1500)
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_wht")), 10)

        # 3nd invoice
        data = [
            {
                "price_unit": 1000.0,
                "wht_tax_id": self.wht_pit.id,
            }
        ]
        invoice3 = self._create_invoice(data)
        invoice3.action_post()

        with Form.from_action(self.env, invoice3.action_register_payment()) as wiz_form:
            self.assertEqual(wiz_form.amount, 970.0)
            self.assertEqual(wiz_form.payment_difference_handling, "reconcile")
            self.assertEqual(wiz_form.payment_difference, 30.0)
            action_payment = wiz_form.save().action_create_payments()

        # Sum up amount_income and withholding amount = 10 + 30 = 40
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_income")), 2500)
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_wht")), 40)

        # Cancel payment
        payment = self.account_payment_obj.browse(action_payment["res_id"])
        self.assertEqual(sum(payment.pit_move_ids.mapped("amount_wht")), 30)
        payment.action_cancel()
        self.assertEqual(sum(payment.pit_move_ids.mapped("amount_wht")), 0)

        # Test calling report for this partner, to get remaining = 10
        res = self.partner.action_view_pit_move_yearly_summary()
        moves = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(sum(moves.mapped("amount_wht")), 10)

        # Test check withholding tax in partner
        action = self.partner.button_wht_certs()
        self.assertEqual(action["domain"][0][2], [])

        # 4th invoice
        data = [
            {
                "price_unit": 400000.0,
                "wht_tax_id": self.wht_pit.id,
            }
        ]
        invoice4 = self._create_invoice(data)
        invoice4.action_post()

        with Form.from_action(self.env, invoice4.action_register_payment()) as wiz_form:
            wiz_form.wht_tax_id = self.wht_pit
            wizard = wiz_form.save()
        self.assertEqual(wizard.writeoff_label, self.wht_pit.display_name)
        res = wizard.action_create_payments()

    def test_03_get_model_move(self):
        """Test send model move to get move lines"""
        data = [
            {
                "price_unit": 500.0,
                "wht_tax_id": self.wht_pit.id,
            }
        ]
        invoice1 = self._create_invoice(data)
        invoice1.action_post()

        result1 = invoice1._get_movelines_from_model("account.move", invoice1.ids)
        result2 = invoice1._get_movelines_from_model(
            "account.move.line", invoice1.line_ids.ids
        )

        self.assertEqual(result1, result2)
