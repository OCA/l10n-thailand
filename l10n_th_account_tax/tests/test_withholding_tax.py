# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, SavepointCase


class TestWithholdingTax(SavepointCase):
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
        cls.account_wht = cls.env["account.withholding.tax"]
        cls.wht_cert = cls.env["withholding.tax.cert"]
        cls.wht_account = cls.account_account.create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "user_type_id": cls.current_asset.id,
                "wht_account": True,
            }
        )
        cls.wht_3 = cls.account_wht.create(
            {
                "name": "Withholding Tax 3%",
                "account_id": cls.wht_account.id,
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
        cls.liquidity_account = cls.account_account.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_liquidity").id,
                ),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.misc_journal = cls.account_journal.search(
            [("type", "=", "general"), ("company_id", "=", cls.env.user.company_id.id)],
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
        wht_amount=0.0,
    ):
        invoice_dict = {
            "name": "Test Supplier Invoice WHT",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "move_type": invoice_type,
            "invoice_date": fields.Date.today(),
        }
        if invoice_type == "entry":
            invoice_dict.update(
                {
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "account_id": line_account_id,  # wht
                                "name": "Test line wht",
                                "credit": wht_amount,
                                "partner_id": partner_id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.liquidity_account.id,
                                "name": "Test line balance",
                                "credit": price_unit - wht_amount,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.expense_account.id,
                                "name": "Test line product",
                                "debit": price_unit,
                            },
                        ),
                    ]
                }
            )
        else:
            invoice_dict.update(
                {
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
            )
        invoice = self.account_move.create(invoice_dict)
        return invoice

    def _register_payment(self, invoice, price_unit):
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice.invoice_line_ids.wht_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        return payment

    def _config_product_withholding_tax(
        self, product_id, account, customer=False, vendor=False
    ):
        if customer:
            product_id.write({"wht_tax_id": account})
        if vendor:
            product_id.write({"supplier_wht_tax_id": account})
        return product_id

    def test_01_create_payment_withholding_tax(self):
        """ Create payment with withholding tax"""
        price_unit = 100.0
        with self.assertRaises(ValidationError):
            self.wht_3.write({"account_id": self.expense_account.id})
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        self.assertFalse(invoice.invoice_line_ids.wht_tax_id)
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        self.assertTrue(invoice.invoice_line_ids.wht_tax_id)
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice.invoice_line_ids.wht_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment_id = self.env[action_payment["res_model"]].browse(
            action_payment["res_id"]
        )
        self.assertEqual(payment_id.state, "posted")
        self.assertEqual(payment_id.amount, price_unit * 0.97)

        # Create WHT Cert from Payment's Action Wizard
        ctx = {
            "active_id": payment_id.id,
            "active_ids": [payment_id.id],
            "active_model": "account.payment",
        }
        res = self.wht_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        f = Form(self.env[res["res_model"]].with_context(res["context"]), view=view)
        wizard = f.save()
        wizard.write({"wht_account_ids": [self.wht_account.id]})
        res = wizard.create_wht_cert()
        # New WHT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"income_tax_form": "pnd3", "wht_cert_income_type": "1"})
        with Form(self.wht_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        cert = f.save()
        self.assertEqual(cert.state, "draft")
        self.assertRecordValues(cert.wht_line, [{"amount": 3.0}])
        payment_id.button_wht_certs()
        cert.action_done()
        self.assertEqual(cert.state, "done")
        # substitute WHT Cert
        wizard.write({"substitute": True, "wht_cert_id": cert})
        res = wizard.create_wht_cert()
        ctx_cert = res.get("context")
        ctx_cert.update({"income_tax_form": "pnd3", "wht_cert_income_type": "1"})
        with Form(self.wht_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        cert2 = f.save()
        self.assertFalse(cert.ref_wht_cert_id)
        self.assertTrue(cert2.ref_wht_cert_id)
        self.assertEqual(cert2.ref_wht_cert_id.id, cert.id)
        self.assertNotEqual(cert2.id, cert.id)
        cert2.action_done()
        self.assertEqual(cert2.state, "done")
        self.assertEqual(cert.state, "cancel")

    def test_02_create_payment_withholding_tax_product(self):
        """ Create payment with withholding tax from product"""
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wht_3.id, vendor=True
        )
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            product_id.id,
        )
        wht_tax_id = invoice.invoice_line_ids.wht_tax_id
        self.assertTrue(wht_tax_id)
        self.assertEqual(wht_tax_id.account_id, self.wht_3.account_id)
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice.invoice_line_ids.wht_tax_id.account_id,
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
        """ Test case withholding tax from customer invoice"""
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wht_3.id, customer=True
        )
        invoice = self._create_invoice(
            self.partner_1.id,
            self.sales_journal.id,
            "out_invoice",
            self.sale_account.id,
            price_unit,
            product_id.id,
        )
        wht_tax_id = invoice.invoice_line_ids.wht_tax_id
        self.assertTrue(wht_tax_id)
        self.assertEqual(wht_tax_id.account_id, self.wht_3.account_id)
        invoice.action_post()

    def test_04_withholding_tax_multi_invoice(self):
        """ Test case withholding tax with multi invoices"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        self.assertFalse(invoice.invoice_line_ids.wht_tax_id)
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        self.assertTrue(invoice.invoice_line_ids.wht_tax_id)
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
            invoice.invoice_line_ids.wht_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, 2 * price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 2 * price_unit * 0.97)

    def test_05_create_wht_cert_journal(self):
        """ Journal Entry to WHT Cert """
        price_unit = 100
        wht_amount = 3
        invoice = self._create_invoice(
            self.partner_1.id,
            self.misc_journal.id,
            "entry",
            self.wht_account.id,
            price_unit,
            wht_amount=wht_amount,
        )
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        # Create WHT Cert from Journal Entry's Action Wizard
        ctx = {
            "active_id": invoice.id,
            "active_ids": [invoice.id],
            "active_model": "account.move",
        }
        res = self.wht_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        f = Form(self.env[res["res_model"]].with_context(res["context"]), view=view)
        wizard = f.save()
        wizard.write({"wht_account_ids": [self.wht_account.id]})
        res = wizard.create_wht_cert()
        # New WHT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"income_tax_form": "pnd3", "wht_cert_income_type": "1"})
        with Form(self.wht_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        wht_cert = f.save()
        self.assertEqual(wht_cert.partner_id, self.partner_1)
        invoice.button_wht_certs()

    def test_06_create_wht_cert_multi_payment(self):
        """ Payments to WHT Certs """
        price_unit = 100
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        invoice2 = invoice.copy()
        invoice2.invoice_date = fields.Date.today()
        invoice.action_post()
        invoice2.action_post()
        payment = self._register_payment(invoice, price_unit)
        payment2 = self._register_payment(invoice2, price_unit)
        # Create WHT Cert from Payment's Action Wizard
        ctx = {
            "active_ids": [payment.id, payment2.id],
            "active_model": "account.payment",
        }
        res = self.wht_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        with Form(
            self.env[res["res_model"]].with_context(res["context"]), view=view
        ) as f:
            f.income_tax_form = "pnd3"
            f.wht_cert_income_type = "1"
        wizard = f.save()
        wizard.write({"wht_account_ids": [self.wht_account.id]})
        res = wizard.create_wht_cert_multi()
        certs = self.wht_cert.search(res["domain"])
        self.assertEqual(len(certs), 2)
        for cert in certs:
            self.assertEqual(cert.wht_line.amount, 3)

    def test_07_create_wht_cert_multi_journal(self):
        """ Journal Entries to WHT Certs """
        price_unit = 100
        wht_amount = 3
        invoice = self._create_invoice(
            self.partner_1.id,
            self.misc_journal.id,
            "entry",
            self.wht_account.id,
            price_unit,
            wht_amount=wht_amount,
        )
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        invoice2 = invoice.copy()
        self.assertEqual(invoice2.state, "draft")
        # Create WHT Cert from Journal Entry's Action Wizard
        ctx = {
            "active_ids": [invoice.id, invoice2.id],
            "active_model": "account.move",
        }
        res = self.wht_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        # Error when create WHT Cert with draft invoice
        with self.assertRaises(UserError):
            with Form(
                self.env[res["res_model"]].with_context(res["context"]), view=view
            ) as f:
                f.income_tax_form = "pnd3"
                f.wht_cert_income_type = "1"
            wizard = f.save()
        invoice2.action_post()
        with Form(
            self.env[res["res_model"]].with_context(res["context"]), view=view
        ) as f:
            f.income_tax_form = "pnd3"
            f.wht_cert_income_type = "1"
        wizard = f.save()
        wizard.write({"wht_account_ids": [self.wht_account.id]})
        res = wizard.create_wht_cert_multi()
        certs = self.wht_cert.search(res["domain"])
        self.assertEqual(len(certs), 2)
        for cert in certs:
            self.assertEqual(cert.wht_line.amount, 3)
