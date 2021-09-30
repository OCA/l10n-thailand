# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, SavepointCase


class TestWithholdingTax(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_model = cls.env["account.payment"]
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.product_1 = cls.env.ref("product.product_product_4")
        cls.current_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.expenses = cls.env.ref("account.data_account_type_expenses")
        cls.revenue = cls.env.ref("account.data_account_type_revenue")
        cls.view_id = "account.view_account_payment_register_form"
        cls.account_move = cls.env["account.move"]
        cls.payment_register = cls.env["account.payment.register"]
        cls.account_account = cls.env["account.account"]
        cls.account_journal = cls.env["account.journal"]
        cls.account_wtax = cls.env["account.withholding.tax"]
        cls.wt_account = cls.account_account.create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "user_type_id": cls.current_asset.id,
                "wt_account": True,
            }
        )
        cls.wt_3 = cls.account_wtax.create(
            {
                "name": "Withholding Tax 3%",
                "account_id": cls.wt_account.id,
                "amount": 3,
            }
        )
        cls.wt_5 = cls.account_wtax.create(
            {
                "name": "Withholding Tax 5%",
                "account_id": cls.wt_account.id,
                "amount": 5,
            }
        )
        cls.expense_account = cls.account_account.search(
            [
                ("user_type_id", "=", cls.expenses.id),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.sale_account = cls.account_account.search(
            [
                ("user_type_id", "=", cls.revenue.id),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.expenses_journal = cls.account_journal.search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.sales_journal = cls.account_journal.search(
            [("type", "=", "sale"), ("company_id", "=", cls.env.user.company_id.id)],
            limit=1,
        )

    def _create_invoice(
        self,
        partner_id,
        journal_id,
        invoice_type,
        line_account_id,
        price_unit,
        product_id=False,
        multi=False,
    ):
        invoice_dict = {
            "name": "Test Supplier Invoice WT",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "move_type": invoice_type,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "quantity": 1.0,
                        "account_id": line_account_id,
                        "name": "Advice1",
                        "price_unit": price_unit or 0.0,
                    },
                )
            ],
        }
        if multi:
            invoice_dict["invoice_line_ids"].append(
                (
                    0,
                    0,
                    {
                        "product_id": product_id,
                        "quantity": 1.0,
                        "account_id": line_account_id,
                        "name": "Advice2",
                        "price_unit": price_unit or 0.0,
                    },
                )
            )
        invoice = self.account_move.create(invoice_dict)
        return invoice

    def _config_product_withholding_tax(
        self, product_id, account, customer=False, vendor=False
    ):
        if customer:
            product_id.write({"wt_tax_id": account})
        if vendor:
            product_id.write({"supplier_wt_tax_id": account})
        return product_id

    def test_01_create_payment_withholding_tax(self):
        price_unit = 100.0
        with self.assertRaises(ValidationError):
            self.wt_3.write({"account_id": self.expense_account.id})
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        invoice2 = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        self.assertFalse(invoice.invoice_line_ids.wt_tax_id)
        invoice.invoice_line_ids.write({"wt_tax_id": self.wt_3.id})
        self.assertTrue(invoice.invoice_line_ids.wt_tax_id)
        invoice.action_post()
        # Test multi invoice and withholding tax in line
        ctx = {
            "active_ids": [invoice.id, invoice2.id],
            "active_model": "account.move",
        }
        with self.assertRaises(UserError):
            f = Form(
                self.payment_register.with_context(ctx),
                view=self.view_id,
            )
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        f = Form(self.payment_register.with_context(ctx), view=self.view_id)
        register_payment = f.save()
        self.assertEqual(register_payment.payment_difference_handling, "reconcile")
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice.invoice_line_ids.wt_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        payment_id = register_payment._create_payments()
        payment = self.payment_model.browse(payment_id.id)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, price_unit * 0.97)

    def test_02_create_payment_multi_withholding_tax_multi_line(self):
        """ Create payment with 2 withholding tax on 2 line"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            multi=True,
        )
        self.assertFalse(invoice.invoice_line_ids.wt_tax_id)
        invoice.invoice_line_ids[0].wt_tax_id = self.wt_3
        invoice.invoice_line_ids[1].wt_tax_id = self.wt_5
        self.assertTrue(invoice.invoice_line_ids.wt_tax_id)
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        f = Form(self.payment_register.with_context(ctx), view=self.view_id)
        register_payment = f.save()
        self.assertEqual(
            register_payment.payment_difference_handling,
            "reconcile_multi_deduct",
        )
        self.assertTrue(register_payment.deduction_ids)
        # Change wt_3 to wt_5
        with self.assertRaises(UserError):
            with Form(register_payment) as f:
                with f.deduction_ids.edit(0) as line:
                    line.wt_tax_id = self.wt_5
        # amount must reducted to 190
        with Form(register_payment) as f:
            with f.deduction_ids.edit(0) as line:
                line.wt_tax_id = self.wt_5
            f.amount = 190
        payment = register_payment._create_payments()
        self.assertEqual(payment.state, "posted")
        self.assertEqual(
            payment.amount,
            (price_unit * 2) - sum(register_payment.deduction_ids.mapped("amount")),
        )

    def test_03_create_payment_one_withholding_tax_multi_line(self):
        """ Create payment with 1 withholding tax on 2 line"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            multi=True,
        )
        self.assertFalse(invoice.invoice_line_ids.wt_tax_id)
        invoice.invoice_line_ids[0].wt_tax_id = self.wt_3
        invoice.invoice_line_ids[1].wt_tax_id = self.wt_3
        self.assertTrue(invoice.invoice_line_ids.mapped("wt_tax_id"))
        invoice.action_post()
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        f = Form(self.payment_register.with_context(ctx), view=self.view_id)
        register_payment = f.save()
        self.assertEqual(
            register_payment.payment_difference_handling,
            "reconcile",
        )
        self.assertFalse(register_payment.deduction_ids)
        payment_id = register_payment._create_payments()
        payment = self.payment_model.browse(payment_id.id)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(
            payment.amount,
            invoice.amount_total - invoice.amount_untaxed * self.wt_3.amount / 100,
        )

    def test_04_create_payment_multi_withholding_keep_open(self):
        """ Create payment with 2 withholding tax on 2 line and keep open 1"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            multi=True,
        )
        self.assertFalse(invoice.invoice_line_ids.wt_tax_id)
        invoice.invoice_line_ids[0].wt_tax_id = self.wt_3
        invoice.invoice_line_ids[1].wt_tax_id = self.wt_5
        self.assertTrue(invoice.invoice_line_ids.mapped("wt_tax_id"))
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        f = Form(self.payment_register.with_context(ctx), view=self.view_id)
        register_payment = f.save()
        self.assertEqual(
            register_payment.payment_difference_handling,
            "reconcile_multi_deduct",
        )
        self.assertTrue(register_payment.deduction_ids)
        # Keep 3% and deduct 5%
        deduct_3 = register_payment.deduction_ids.filtered(
            lambda l: l.wt_tax_id == self.wt_3
        )
        with Form(deduct_3) as deduct:
            deduct.open = True
        self.assertFalse(deduct.wt_tax_id)
        payment_id = register_payment._create_payments()
        payment = self.payment_model.browse(payment_id.id)
        self.assertEqual(len(payment.line_ids.mapped("move_id")), 1)
        # cehck reconcile
        self.assertEqual(invoice.payment_state, "partial")
        self.assertFalse(payment.line_ids.mapped("full_reconcile_id"))
        # paid residual, it should be reconcile
        with Form(self.payment_register.with_context(ctx), view=self.view_id) as f:
            f.amount = 0
            f.deduction_ids.remove(index=1)
        register_payment = f.save()
        register_payment.action_create_payments()
        self.assertEqual(invoice.payment_state, "paid")
        self.assertTrue(payment.line_ids.mapped("full_reconcile_id"))

    # TODO: test for PIT cases
