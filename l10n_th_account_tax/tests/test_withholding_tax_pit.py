# Copyright 2021 Ecosoft Co., Ltd. <http://ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, TransactionCase


class TestWithholdingTaxPIT(TransactionCase):
    @classmethod
    @freeze_time("2001-02-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test", "standard_price": 500.0}
        )
        cls.RegisterPayment = cls.env["account.payment.register"]
        # Setup PIT withholding tax
        cls.account_pit = cls.env["account.account"].create(
            {
                "code": "100",
                "name": "Personal Income Tax",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
                "wht_account": True,
            }
        )
        cls.wht_pit = cls.env["account.withholding.tax"].create(
            {
                "name": "PIT",
                "account_id": cls.account_pit.id,
                "is_pit": True,
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
        data = [{"amount": 1, "pit": True}, ...]
        """
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(self.env.user)
        move_form.partner_id = self.partner
        for line in data:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product
                line_form.price_unit = line["amount"]
                line_form.wht_tax_id = (
                    line["pit"] and self.wht_pit or self.env["account.withholding.tax"]
                )
                for i in range(len(line_form.tax_ids)):
                    line_form.tax_ids.remove(index=i)
        return move_form.save()

    def test_00_pit_tax(self):
        """No 2 PIT Tax allowed"""
        with self.assertRaises(ValidationError):
            self.wht_pit = self.env["account.withholding.tax"].create(
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
            pit_rate_copy.calendar_year, "{} (copy)".format(self.pit_rate.calendar_year)
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
        data = [{"amount": 500, "pit": True}, {"amount": 1500, "pit": False}]
        self.invoice = self._create_invoice(data)
        self.invoice.action_post()
        res = self.invoice.action_register_payment()
        # Register payment, without PIT rate yet
        with self.assertRaises(UserError):
            form = Form(self.RegisterPayment.with_context(**res["context"]))
        # Create an effective PIT Rate, and try again.
        self.pit_rate = self._create_pit("2001")
        with Form(self.RegisterPayment.with_context(**res["context"])) as f:
            f.wht_tax_id = self.wht_pit  # Test refreshing wht_tax_id
        wizard = f.save()
        wizard.action_create_payments()
        # PIT created but not PIT amount yet.
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_income")), 500)
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_wht")), 0)

        # 2nd invoice
        data = [{"amount": 1000, "pit": True}]
        self.invoice = self._create_invoice(data)
        self.invoice.action_post()
        res = self.invoice.action_register_payment()
        form = Form(self.RegisterPayment.with_context(**res["context"]))
        wizard = form.save()
        wizard.action_create_payments()
        # Sum up amount_income and withholding amount = 10
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_income")), 1500)
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_wht")), 10)

        # 3nd invoice
        data = [{"amount": 1000, "pit": True}]
        self.invoice = self._create_invoice(data)
        self.invoice.action_post()
        res = self.invoice.action_register_payment()
        form = Form(self.RegisterPayment.with_context(**res["context"]))
        wizard = form.save()
        res = wizard.action_create_payments()
        # Sum up amount_income and withholding amount = 10 + 30 = 40
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_income")), 2500)
        self.assertEqual(sum(self.partner.pit_move_ids.mapped("amount_wht")), 40)
        # Cancel payment
        payment = self.env[res["res_model"]].browse(res["res_id"])
        self.assertEqual(sum(payment.pit_move_ids.mapped("amount_wht")), 30)
        payment.action_cancel()
        self.assertEqual(sum(payment.pit_move_ids.mapped("amount_wht")), 0)
        # Test calling report for this partner, to get remaining = 10
        res = self.partner.action_view_pit_move_yearly_summary()
        moves = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(sum(moves.mapped("amount_wht")), 10)
