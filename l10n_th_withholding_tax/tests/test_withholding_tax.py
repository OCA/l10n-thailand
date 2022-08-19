# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, TransactionCase


class TestWithholdingTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.product_1 = cls.env.ref("product.product_product_4")
        cls.current_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.expenses = cls.env.ref("account.data_account_type_expenses")
        cls.revenue = cls.env.ref("account.data_account_type_revenue")
        cls.register_view_id = "account.view_account_payment_register_form"
        cls.account_move = cls.env["account.move"]
        cls.account_payment_register = cls.env["account.payment.register"]
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
                        "name": "Advice",
                        "price_unit": price_unit or 0.0,
                    },
                )
            ],
        }
        invoice_id = self.account_move.create(invoice_dict)
        return invoice_id

    def _config_product_withholding_tax(
        self, product_id, account, customer=False, vendor=False
    ):
        if customer:
            product_id.write({"wt_tax_id": account})
        if vendor:
            product_id.write({"supplier_wt_tax_id": account})
        return product_id

    def test_01_create_payment_withholding_tax(self):
        """Create payment with withholding tax"""
        price_unit = 100.0
        with self.assertRaises(ValidationError):
            self.wt_3.write({"account_id": self.expense_account.id})
        invoice_id = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        self.assertFalse(invoice_id.invoice_line_ids.wt_tax_id)
        invoice_id.invoice_line_ids.write({"wt_tax_id": self.wt_3.id})
        self.assertTrue(invoice_id.invoice_line_ids.wt_tax_id)
        invoice_id.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice_id.id],
            "active_id": invoice_id.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice_id.invoice_line_ids.wt_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment_id = self.env[action_payment["res_model"]].browse(
            action_payment["res_id"]
        )
        self.assertEqual(payment_id.state, "posted")
        self.assertEqual(payment_id.amount, price_unit * 0.97)

    def test_02_create_payment_withholding_tax_product(self):
        """Create payment with withholding tax from product"""
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wt_3.id, vendor=True
        )
        invoice_id = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            product_id.id,
        )
        wt_tax_id = invoice_id.invoice_line_ids.wt_tax_id
        self.assertTrue(wt_tax_id)
        self.assertEqual(wt_tax_id.account_id, self.wt_3.account_id)
        invoice_id.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice_id.id],
            "active_id": invoice_id.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice_id.invoice_line_ids.wt_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment_id = self.env[action_payment["res_model"]].browse(
            action_payment["res_id"]
        )
        self.assertEqual(payment_id.state, "posted")
        self.assertEqual(payment_id.amount, price_unit * 0.97)

    def test_03_withholding_tax_customer_invoice(self):
        """Test case withholding tax from customer invoice"""
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wt_3.id, customer=True
        )
        invoice_id = self._create_invoice(
            self.partner_1.id,
            self.sales_journal.id,
            "out_invoice",
            self.sale_account.id,
            price_unit,
            product_id.id,
        )
        wt_tax_id = invoice_id.invoice_line_ids.wt_tax_id
        self.assertTrue(wt_tax_id)
        self.assertEqual(wt_tax_id.account_id, self.wt_3.account_id)
        invoice_id.action_post()

    def test_04_withholding_tax_multi_invoice(self):
        """Test case withholding tax with multi invoices"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        self.assertFalse(invoice.invoice_line_ids.wt_tax_id)
        invoice.invoice_line_ids.write({"wt_tax_id": self.wt_3.id})
        self.assertTrue(invoice.invoice_line_ids.wt_tax_id)
        # Duplicate invoice
        invoice_dict = {
            "invoice1": invoice.copy(),
            "invoice2": invoice.copy(),
            "invoice3": invoice.copy(),
        }
        for k in invoice_dict.keys():
            invoice_dict[k]["invoice_date"] = fields.Date.today()
        invoice_dict["invoice3"]["partner_id"] = (self.partner_2.id,)
        for invoice in invoice_dict.values():
            invoice.action_post()
        # Test multi partners
        ctx = {
            "active_ids": [invoice_dict["invoice1"].id, invoice_dict["invoice3"].id],
            "active_model": "account.move",
        }
        with self.assertRaises(UserError):
            with Form(
                self.account_payment_register.with_context(ctx),
                view=self.register_view_id,
            ) as f:
                register_payment = f.save()
            register_payment.action_create_payments()
        # Test same partner and not group payments
        ctx = {
            "active_ids": [invoice_dict["invoice1"].id, invoice_dict["invoice2"].id],
            "active_model": "account.move",
        }
        with self.assertRaises(UserError):
            with Form(
                self.account_payment_register.with_context(ctx),
                view=self.register_view_id,
            ) as f:
                register_payment = f.save()
            register_payment.group_payment = False
            register_payment.action_create_payments()
        # Test same partner and group payments
        ctx = {
            "active_ids": [invoice_dict["invoice1"].id, invoice_dict["invoice2"].id],
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice.invoice_line_ids.wt_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, 2 * price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 2 * price_unit * 0.97)
