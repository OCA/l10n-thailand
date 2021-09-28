# Copyright 2021 Ecosoft Co., Ltd. <http://ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestWithholdingTaxPIT(TransactionCase):
    @freeze_time("2001-02-01")
    def setUp(self):
        super(TestWithholdingTaxPIT, self).setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.product = self.env["product.product"].create(
            {"name": "Test", "standard_price": 500.0}
        )
        self.RegisterPayment = self.env["account.payment.register"]
        # Setup PIT withholding tax
        self.account_pit = self.env["account.account"].create(
            {
                "code": "100",
                "name": "Personal Income Tax",
                "user_type_id": self.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
                "wt_account": True,
            }
        )
        self.wt_pit = self.env["account.withholding.tax"].create(
            {
                "name": "PIT",
                "account_id": self.account_pit.id,
                "account_pit": True,
            }
        )
        with Form(self.env["personal.income.tax"]) as f:
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
        self.pit_rate = f.save()

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
                line_form.wt_tax_id = (
                    line["pit"] and self.wt_pit or self.env["account.withholding.tax"]
                )
        return move_form.save()

    @freeze_time("2001-02-01")
    def test_01_pit_rate(self):
        """ Test PIT Rate table """
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
        form = Form(self.RegisterPayment.with_context(res["context"]))
        wizard = form.save()
        wizard.action_create_payments()
        # PIT created but not PIT amount yet.
        self.assertEqual(sum(self.partner.pit_line.mapped("amount_income")), 500)
        self.assertEqual(sum(self.partner.pit_line.mapped("amount_wt")), 0)

        # 2nd invoice
        data = [{"amount": 1000, "pit": True}]
        self.invoice = self._create_invoice(data)
        self.invoice.action_post()
        res = self.invoice.action_register_payment()
        form = Form(self.RegisterPayment.with_context(res["context"]))
        wizard = form.save()
        wizard.action_create_payments()
        # Sum up amount_income and withholding amount = 10
        self.assertEqual(sum(self.partner.pit_line.mapped("amount_income")), 1500)
        self.assertEqual(sum(self.partner.pit_line.mapped("amount_wt")), 10)

        # 3nd invoice
        data = [{"amount": 1000, "pit": True}]
        self.invoice = self._create_invoice(data)
        self.invoice.action_post()
        res = self.invoice.action_register_payment()
        form = Form(self.RegisterPayment.with_context(res["context"]))
        wizard = form.save()
        wizard.action_create_payments()
        # Sum up amount_income and withholding amount = 10 + 30 = 40
        self.assertEqual(sum(self.partner.pit_line.mapped("amount_income")), 2500)
        self.assertEqual(sum(self.partner.pit_line.mapped("amount_wt")), 40)

        # Print Cert
        ctx = {"active_model": "res.partner", "active_id": self.partner.id}
        form = Form(self.env["create.pit.withholding.tax.cert"].with_context(ctx))
        form.date_from = "2001-01-01"
        form.date_to = "2001-12-31"
        form.income_tax_form = "pnd1"
        wizard = form.save()
        # Not yet, fill the income type
        with self.assertRaises(UserError):
            res = wizard.create_pit_wt_cert()
        # Fill in income type
        self.partner.pit_line.write({"wt_cert_income_type": "1"})
        res = wizard.create_pit_wt_cert()
        cert_id = res["domain"][0][2][0]
        cert = self.env["withholding.tax.cert"].browse(cert_id)
        self.assertEqual(sum(cert.wt_line.mapped("amount")), 40)
