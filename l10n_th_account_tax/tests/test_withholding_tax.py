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
        cls.currency_eur = cls.env.ref("base.EUR")
        cls.currency_usd = cls.env.ref("base.USD")
        cls.currency_rate = cls.env["res.currency.rate"]
        cls.main_company = cls.env.ref("base.main_company")
        cls.register_view_id = "account.view_account_payment_register_form"
        cls.account_move = cls.env["account.move"]
        cls.account_payment_register = cls.env["account.payment.register"]
        cls.account_payment = cls.env["account.payment"]
        cls.account_account = cls.env["account.account"]
        cls.account_journal = cls.env["account.journal"]
        cls.account_wht = cls.env["account.withholding.tax"]
        cls.wht_income_code_402I = cls.env.ref(
            "l10n_th_account_tax.withholding_tax_pnd1_402I"
        )
        cls.wht_income_code_402E = cls.env.ref(
            "l10n_th_account_tax.withholding_tax_pnd1_402E"
        )
        cls.wht_cert = cls.env["withholding.tax.cert"]
        cls.wht_account = cls.account_account.create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "account_type": "asset_current",
                "wht_account": True,
            }
        )
        cls.wht_1 = cls.account_wht.create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.wht_account.id,
                "amount": 1,
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
                ("account_type", "=", "expense"),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.sale_account = cls.account_account.search(
            [
                ("account_type", "=", "income"),
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
                ("account_type", "=", "asset_cash"),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.misc_journal = cls.account_journal.search(
            [("type", "=", "general"), ("company_id", "=", cls.env.user.company_id.id)],
            limit=1,
        )
        # SetUp currency and rates 1 Euro = 2$
        cls.env.cr.execute(
            """UPDATE res_company SET currency_id = %s""",
            [cls.currency_eur.id],
        )
        cls.currency_rate.search([]).unlink()
        cls.currency_rate.create(
            {
                "name": "2020-01-01",
                "rate": 1.0,
                "currency_id": cls.currency_eur.id,
                "company_id": cls.main_company.id,
            }
        )

        cls.currency_rate.create(
            {
                "name": "2020-01-01",
                "rate": 2,
                "currency_id": cls.currency_usd.id,
                "company_id": cls.main_company.id,
            }
        )

    def _create_invoice(
        self,
        partner_id,
        journal_id,
        move_type,
        line_account_id,
        price_unit,
        product_id=False,
        wht_amount=0.0,
        wht_tax_id=False,
    ):
        invoice_dict = {
            "name": "/",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "move_type": move_type,
            "invoice_date": fields.Date.today(),
        }
        if move_type == "entry":
            invoice_dict.update(
                {
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "account_id": line_account_id,  # wht
                                "wht_tax_id": wht_tax_id,
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
                                "tax_ids": False,  # Clear all taxes
                            },
                        )
                    ],
                }
            )
        invoice = self.account_move.create(invoice_dict)
        return invoice

    def _config_product_withholding_tax(
        self, product_id, account, customer=False, vendor=False
    ):
        if customer:
            product_id.write({"wht_tax_id": account})
        if vendor:
            product_id.write(
                {"supplier_wht_tax_id": account, "supplier_company_wht_tax_id": account}
            )
        return product_id

    def test_01_create_payment_withholding_tax(self):
        """Create payment with withholding tax"""
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
        # Test Change WHT to 1%
        with Form(
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            f.wht_tax_id = self.wht_1
        register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            self.wht_1.account_id,
        )
        self.assertEqual(
            register_payment.writeoff_label,
            self.wht_1.display_name,
        )
        self.assertEqual(
            register_payment.amount, price_unit - (price_unit * 0.01)
        )  # WHT 1%
        # Change back to 3%
        with Form(
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            f.wht_tax_id = self.wht_3
        register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice.invoice_line_ids.wht_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, price_unit * 0.97)
        self.assertFalse(payment.wht_certs_count)
        # Check no update income type on payment, it should error
        with self.assertRaises(UserError):
            payment.create_wht_cert()
        # Create WHT Cert from Payment
        payment.wht_move_ids.write({"wht_cert_income_type": "1"})
        payment.create_wht_cert()
        self.assertEqual(payment.wht_certs_count, 1)
        # Open WHT certs
        res = payment.button_wht_certs()
        cert = self.wht_cert.search(res["domain"])
        self.assertEqual(cert.state, "draft")
        self.assertEqual(cert.name, payment.name)
        self.assertEqual(cert.date, payment.date)
        self.assertRecordValues(cert.wht_line, [{"amount": 3.0}])
        payment.button_wht_certs()
        with Form(cert) as c:
            c.income_tax_form = "pnd1"
        cert_line = cert.wht_line
        self.assertEqual(len(cert_line), 1)
        self.assertEqual(cert_line.wht_percent, 3.0)
        # Test add default income code more than 1, it should error
        self.wht_income_code_402I.is_default = True
        with self.assertRaises(UserError):
            self.wht_income_code_402E.is_default = True
        with Form(cert_line) as line:
            line.wht_cert_income_type = "2"
        self.assertEqual(cert_line.wht_cert_income_code, self.wht_income_code_402I)
        self.assertEqual(
            cert_line.wht_cert_income_desc, "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)"
        )

        cert.action_done()
        self.assertEqual(cert.state, "done")
        # After done, can draft withholding tax
        cert.action_draft()
        self.assertEqual(cert.state, "draft")

    def test_02_create_payment_withholding_tax_product(self):
        """Create payment with withholding tax from product"""
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
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
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
        """Test case withholding tax from customer invoice"""
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
        """Test case withholding tax with multi invoices"""
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
        # Post invoice
        for invoice in invoice_dict.values():
            invoice.action_post()
        # Test multi partners
        ctx = {
            "active_ids": [invoice_dict["invoice1"].id, invoice_dict["invoice3"].id],
            "active_model": "account.move",
        }
        with self.assertRaises(UserError):
            Form(
                self.account_payment_register.with_context(**ctx),
                view=self.register_view_id,
            )
        # Test same partner and not group payments
        ctx = {
            "active_ids": [invoice_dict["invoice1"].id, invoice_dict["invoice2"].id],
            "active_model": "account.move",
        }
        with self.assertRaises(UserError):
            with Form(
                self.account_payment_register.with_context(**ctx),
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
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            register_payment = f.save()
        self.assertEqual(
            register_payment.writeoff_account_id,
            invoice_dict["invoice1"].invoice_line_ids.wht_tax_id.account_id,
        )
        self.assertEqual(register_payment.payment_difference, 2 * price_unit * 0.03)
        self.assertEqual(register_payment.writeoff_label, "Withholding Tax 3%")
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, 2 * price_unit * 0.97)

    def test_05_create_wht_cert_journal(self):
        """Journal Entry to WHT Cert"""
        price_unit = 100
        wht_amount = 3
        invoice = self._create_invoice(
            self.partner_1.id,
            self.misc_journal.id,
            "entry",
            self.wht_account.id,
            price_unit,
            wht_amount=wht_amount,
            wht_tax_id=self.wht_3.id,
        )
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.wht_cert_status, "none")
        # Check default wht income type
        invoice.wht_move_ids._compute_wht_cert_income_type()
        self.assertFalse(invoice.wht_move_ids.wht_cert_income_type)
        # Create WHT Cert from Payment
        invoice.wht_move_ids.write({"wht_cert_income_type": "1"})
        invoice.create_wht_cert()
        self.assertTrue(invoice.wht_cert_ids)
        self.assertEqual(invoice.wht_cert_status, "draft")
        # Open WHT certs
        res = invoice.button_wht_certs()
        cert = self.wht_cert.search(res["domain"])
        self.assertEqual(cert.partner_id, self.partner_1)
        # Check wht cert status in invoice
        cert.action_cancel()
        self.assertEqual(invoice.wht_cert_status, "cancel")
        cert.action_done()
        self.assertEqual(invoice.wht_cert_status, "done")

        # Test Create new WHT for related old WHT
        invoice2 = self._create_invoice(
            self.partner_1.id,
            self.misc_journal.id,
            "entry",
            self.wht_account.id,
            price_unit,
            wht_amount=wht_amount,
            wht_tax_id=self.wht_3.id,
        )
        invoice2.action_post()
        invoice2.wht_move_ids.write({"wht_cert_income_type": "1"})
        invoice2.create_wht_cert()
        res = invoice2.button_wht_certs()
        cert2 = self.wht_cert.search(res["domain"])
        cert2.ref_wht_cert_id = cert.id
        # After done new WHT. it will change state old WHT to cancel
        self.assertEqual(cert.state, "done")
        cert2.action_done()
        self.assertEqual(cert.state, "cancel")
        self.assertEqual(cert2.state, "done")

    def test_06_create_withholding_tax_multi_currency(self):
        """Create payment with withholding tax multi currency"""
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
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        # Test change currency in wizard register
        with Form(
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            f.currency_id = self.currency_usd
            f.wht_tax_id = self.wht_1
        register_payment = f.save()
        self.assertEqual(
            register_payment.amount, (price_unit - (price_unit * 0.01)) * 2
        )

        # Test change currency move
        invoice.currency_id = self.currency_usd.id
        with Form(
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            f.currency_id = self.currency_eur
            f.wht_tax_id = self.wht_1
        self.assertEqual(
            register_payment.amount, (price_unit - (price_unit * 0.01)) * 2
        )
