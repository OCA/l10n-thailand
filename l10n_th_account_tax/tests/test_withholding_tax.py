# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestWithholdingTax(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.move_obj = cls.env["account.move"]
        cls.wiz_payment_register_obj = cls.env["account.payment.register"]
        cls.account_account_obj = cls.env["account.account"]
        cls.journal_obj = cls.env["account.journal"]
        cls.account_wht_obj = cls.env["account.withholding.tax"]
        cls.wht_cert_obj = cls.env["withholding.tax.cert"]

        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.product_1 = cls.env.ref("product.product_product_4")

        # Main currency is USD, EUR is multi-currency
        cls.currency_usd = cls.env.ref("base.USD")
        cls.other_currency = cls.setup_other_currency("EUR")

        cls.main_company = cls.env.ref("base.main_company")
        cls.wht_income_code_402I = cls.env.ref(
            "l10n_th_account_tax.withholding_tax_pnd1_402I"
        )
        cls.wht_income_code_402E = cls.env.ref(
            "l10n_th_account_tax.withholding_tax_pnd1_402E"
        )
        cls.wht_account = cls.account_account_obj.create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "account_type": "asset_current",
                "wht_account": True,
            }
        )
        cls.wht_1 = cls.account_wht_obj.create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.wht_account.id,
                "amount": 1,
            }
        )
        cls.wht_3 = cls.account_wht_obj.create(
            {
                "name": "Withholding Tax 3%",
                "account_id": cls.wht_account.id,
                "amount": 3,
            }
        )
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.sale_account = cls.company_data["default_account_revenue"]
        cls.purchase_journal = cls.company_data["default_journal_purchase"]
        cls.sales_journal = cls.company_data["default_journal_sale"]
        cls.journal_bank = cls.company_data["default_journal_bank"]
        cls.misc_journal = cls.company_data["default_journal_misc"]
        cls.liquidity_account = cls.account_account_obj.search(
            [
                ("account_type", "=", "asset_cash"),
            ],
            limit=1,
        )

        # SetUp currency and rates 2 Euro = 1$
        cls.other_currency.rate_ids.sorted()[0].write({"rate": 2.0})

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
                        Command.create(
                            {
                                "account_id": line_account_id,  # wht
                                "wht_tax_id": wht_tax_id,
                                "name": "Test line wht",
                                "credit": wht_amount,
                                "partner_id": partner_id,
                            },
                        ),
                        Command.create(
                            {
                                "account_id": self.liquidity_account.id,
                                "name": "Test line balance",
                                "credit": price_unit - wht_amount,
                            },
                        ),
                        Command.create(
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
                        Command.create(
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
        invoice = self.move_obj.create(invoice_dict)
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
            self.purchase_journal.id,
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
            "active_ids": invoice.line_ids.ids,
            "active_model": "account.move.line",
        }
        # Test Change WHT to 1%
        with Form(
            self.wiz_payment_register_obj.with_context(**ctx),
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
            self.wiz_payment_register_obj.with_context(**ctx),
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
        self.assertEqual(payment.state, "in_process")
        self.assertEqual(payment.amount, price_unit * 0.97)
        self.assertFalse(payment.wht_certs_count)
        # Allow create WHT Cert, but not yet
        self.assertEqual(payment.wht_cert_status, "none")
        # Check no update income type on payment, it should error
        with self.assertRaises(UserError):
            payment.create_wht_cert()
        # Create WHT Cert from Payment
        payment.wht_move_ids.write({"wht_cert_income_type": "1"})
        payment.create_wht_cert()

        # WHT Cert created, wht cert status should change to draft
        self.assertEqual(payment.wht_cert_status, "draft")
        self.assertEqual(payment.wht_certs_count, 1)
        # Open WHT certs
        res = payment.button_wht_certs()
        cert = self.wht_cert_obj.search(res["domain"])
        self.assertEqual(cert.state, "draft")
        self.assertEqual(cert.number, "/")
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
        self.assertFalse(cert.verify_by)

        cert.action_done()
        self.assertEqual(cert.state, "done")
        self.assertNotEqual(cert.number, "/")
        self.assertEqual(cert.verify_by, self.env.user)

        # WHT Cert created and done, wht cert status should change to done
        self.assertEqual(payment.wht_cert_status, "done")
        # After done, can draft withholding tax
        cert.action_draft()
        self.assertEqual(cert.state, "draft")
        self.assertNotEqual(cert.number, "/")
        self.assertFalse(cert.verify_by)
        # WHT Cert cancel, wht cert status should change to cancel
        cert.action_cancel()
        self.assertEqual(cert.state, "cancel")
        self.assertEqual(payment.wht_cert_status, "cancel")
        self.assertFalse(cert.verify_by)

    def test_02_create_payment_withholding_tax_product(self):
        """Create payment with withholding tax from product"""
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wht_3.id, vendor=True
        )
        invoice = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
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
            "active_ids": invoice.line_ids.ids,
            "active_model": "account.move.line",
        }
        register_payment = Form(
            self.wiz_payment_register_obj.with_context(**ctx),
        ).save()
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
        self.assertEqual(payment_id.state, "in_process")
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

        with Form.from_action(self.env, invoice.action_register_payment()) as wiz_form:
            action_payment = wiz_form.save().action_create_payments()

        # After register payment with withholding tax,
        # it should not have withholding tax in payment
        payment = self.env["account.payment"].browse(action_payment["res_id"])
        self.assertFalse(payment.has_wht)
        self.assertFalse(payment.wht_cert_status)

        self.assertFalse(payment.move_id.has_wht)
        self.assertFalse(payment.move_id.wht_cert_status)

    def test_04_withholding_tax_multi_invoice(self):
        """Test case withholding tax with multi invoices"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
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
            "active_ids": (
                invoice_dict["invoice1"].line_ids + invoice_dict["invoice3"].line_ids
            ).ids,
            "active_model": "account.move.line",
        }
        with self.assertRaises(UserError):
            Form(
                self.wiz_payment_register_obj.with_context(**ctx),
            )
        # Test same partner and not group payments
        ctx = {
            "active_ids": (
                invoice_dict["invoice1"].line_ids + invoice_dict["invoice2"].line_ids
            ).ids,
            "active_model": "account.move.line",
        }
        with self.assertRaises(UserError):
            with Form(
                self.wiz_payment_register_obj.with_context(**ctx),
            ) as f:
                register_payment = f.save()
            register_payment.group_payment = False
            register_payment.action_create_payments()
        # Test same partner and group payments
        ctx = {
            "active_ids": (
                invoice_dict["invoice1"].line_ids + invoice_dict["invoice2"].line_ids
            ).ids,
            "active_model": "account.move.line",
        }
        with Form(
            self.wiz_payment_register_obj.with_context(**ctx),
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
        self.assertEqual(payment.state, "in_process")
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
        cert = self.wht_cert_obj.search(res["domain"])
        self.assertEqual(cert.partner_id, self.partner_1)
        self.assertEqual(cert.number, "/")
        # Check wht cert status in invoice
        cert.action_cancel()
        self.assertEqual(invoice.wht_cert_status, "cancel")
        self.assertEqual(cert.number, "/")
        cert.action_done()
        self.assertEqual(invoice.wht_cert_status, "done")
        self.assertNotEqual(cert.number, "/")

        # Number should be generate 1 time only
        cert.action_draft()
        cert.action_done()
        self.assertNotEqual(cert.number, "/")

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
        cert2 = self.wht_cert_obj.search(res["domain"])
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
            self.purchase_journal.id,
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
            "active_ids": invoice.line_ids.ids,
            "active_model": "account.move.line",
        }
        # Test change currency in wizard register
        with Form(
            self.wiz_payment_register_obj.with_context(**ctx),
        ) as f:
            f.currency_id = self.other_currency
            f.wht_tax_id = self.wht_1
        register_payment = f.save()
        self.assertEqual(
            register_payment.amount, (price_unit - (price_unit * 0.01)) * 2
        )

        # Test change currency move
        invoice.button_draft()
        invoice.currency_id = self.other_currency.id
        invoice.action_post()
        with Form(
            self.wiz_payment_register_obj.with_context(**ctx),
        ) as f:
            f.currency_id = self.currency_usd
            f.wht_tax_id = self.wht_1
        self.assertEqual(
            register_payment.amount, (price_unit - (price_unit * 0.01)) * 2
        )
