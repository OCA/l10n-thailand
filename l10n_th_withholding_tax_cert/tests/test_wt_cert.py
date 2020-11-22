# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, SavepointCase


class TestWTCert(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.register_view_id = "account.view_account_payment_register_form"
        cls.account_move = cls.env["account.move"]
        cls.account_payment_register = cls.env["account.payment.register"]
        cls.account_account = cls.env["account.account"]
        cls.account_journal = cls.env["account.journal"]
        cls.wt_cert = cls.env["withholding.tax.cert"]
        cls.account_wtax = cls.env["account.withholding.tax"]
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.current_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.expenses = cls.env.ref("account.data_account_type_expenses")
        cls.revenue = cls.env.ref("account.data_account_type_revenue")
        cls.liquidity = cls.env.ref("account.data_account_type_liquidity")
        cls.currency_usd = cls.env.ref("base.USD")
        cls.main_company = cls.env.ref("base.main_company")
        cls.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (cls.main_company.id, cls.currency_usd.id),
        )
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
                ("company_id", "=", cls.main_company.id),
            ],
            limit=1,
        )
        cls.sale_account = cls.account_account.search(
            [
                ("user_type_id", "=", cls.revenue.id),
                ("company_id", "=", cls.main_company.id),
            ],
            limit=1,
        )
        cls.liquidity_account = cls.account_account.search(
            [
                ("user_type_id", "=", cls.liquidity.id),
                ("company_id", "=", cls.main_company.id),
            ],
            limit=1,
        )
        cls.expenses_journal = cls.account_journal.search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", cls.main_company.id),
            ],
            limit=1,
        )
        cls.sales_journal = cls.account_journal.search(
            [("type", "=", "sale"), ("company_id", "=", cls.main_company.id)],
            limit=1,
        )
        cls.bank_journal = cls.account_journal.search(
            [("type", "=", "bank"), ("company_id", "=", cls.main_company.id)],
            limit=1,
        )
        cls.misc_journal = cls.account_journal.search(
            [("type", "=", "general"), ("company_id", "=", cls.main_company.id)],
            limit=1,
        )

    def _create_invoice(self, partner_id, journal_id, invoice_type, wt_account=False):
        invoice_dict = {
            "name": "Test Supplier Invoice WT",
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
                                "account_id": wt_account.id,
                                "partner_id": self.partner_1.id,
                                "name": "Test line wht",
                                "credit": 3.00,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.liquidity_account.id,
                                "partner_id": self.partner_1.id,
                                "name": "Test line credit",
                                "credit": 97.00,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.expense_account.id,
                                "partner_id": self.partner_1.id,
                                "name": "Test line debit",
                                "debit": 100.00,
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
                                "quantity": 1.0,
                                "account_id": self.expense_account.id,
                                "name": "Advice",
                                "price_unit": 100.00,
                            },
                        )
                    ]
                }
            )
        invoice = self.account_move.create(invoice_dict)
        return invoice

    def _register_payment(self, invoice):
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(ctx), view=self.register_view_id
        ) as f:
            f.journal_id = self.bank_journal
            f.amount = 97.0  # To withhold 3.0
            f.payment_difference_handling = "reconcile"
            f.writeoff_account_id = self.wt_account
            f.writeoff_label = "Withhold 3%"
        register_payment = f.save()
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        return payment

    def test_01_create_wt_cert_payment(self):
        """ Payment to WT Cert """
        invoice = self._create_invoice(
            self.partner_1.id, self.expenses_journal.id, "in_invoice"
        )
        invoice.action_post()
        payment = self._register_payment(invoice)
        # Create WT Cert from Payment's Action Wizard
        ctx = {
            "active_id": payment.id,
            "active_ids": [payment.id],
            "active_model": "account.payment",
        }
        res = self.wt_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        f = Form(self.env[res["res_model"]].with_context(res["context"]), view=view)
        wizard = f.save()
        wizard.write({"wt_account_ids": [self.wt_account.id]})
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"income_tax_form": "pnd3", "wt_cert_income_type": "1"})
        with Form(self.wt_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        cert = f.save()
        self.assertEqual(cert.state, "draft")
        self.assertRecordValues(cert.wt_line, [{"amount": 3.0}])
        payment.button_wt_certs()
        cert.action_done()
        self.assertEqual(cert.state, "done")
        # substitute WT Cert
        wizard.write({"substitute": True, "wt_cert_id": cert})
        res = wizard.create_wt_cert()
        ctx_cert = res.get("context")
        ctx_cert.update({"income_tax_form": "pnd3", "wt_cert_income_type": "1"})
        with Form(self.wt_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        cert2 = f.save()
        self.assertFalse(cert.ref_wt_cert_id)
        self.assertTrue(cert2.ref_wt_cert_id)
        self.assertEqual(cert2.ref_wt_cert_id.id, cert.id)
        self.assertNotEqual(cert2.id, cert.id)
        cert2.action_done()
        self.assertEqual(cert2.state, "done")
        self.assertEqual(cert.state, "cancel")

    def test_02_create_wt_cert_je(self):
        """ Journal Entry to WT Cert """
        invoice = self._create_invoice(
            False, self.misc_journal.id, "entry", self.wt_account
        )
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        # Create WT Cert from Journal Entry's Action Wizard
        ctx = {
            "active_id": invoice.id,
            "active_ids": [invoice.id],
            "active_model": "account.move",
        }
        res = self.wt_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        f = Form(self.env[res["res_model"]].with_context(res["context"]), view=view)
        wizard = f.save()
        wizard.write({"wt_account_ids": [self.wt_account.id]})
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"income_tax_form": "pnd3", "wt_cert_income_type": "1"})
        with Form(self.wt_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        wt_cert = f.save()
        self.assertEqual(wt_cert.supplier_partner_id, self.partner_1)
        invoice.button_wt_certs()

    def test_03_create_wt_cert_payment_multi(self):
        """ Payments to WT Certs """
        invoice = self._create_invoice(
            self.partner_1.id, self.expenses_journal.id, "in_invoice"
        )
        invoice2 = invoice.copy()
        invoice2.invoice_date = fields.Date.today()
        invoice.action_post()
        invoice2.action_post()
        payment = self._register_payment(invoice)
        payment2 = self._register_payment(invoice2)
        # Create WT Cert from Payment's Action Wizard
        ctx = {
            "active_ids": [payment.id, payment2.id],
            "active_model": "account.payment",
        }
        res = self.wt_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        with Form(
            self.env[res["res_model"]].with_context(res["context"]), view=view
        ) as f:
            f.income_tax_form = "pnd3"
            f.wt_cert_income_type = "1"
        wizard = f.save()
        wizard.write({"wt_account_ids": [self.wt_account.id]})
        res = wizard.create_wt_cert_multi()
        certs = self.wt_cert.search(res["domain"])
        self.assertEqual(len(certs), 2)
        for cert in certs:
            self.assertEqual(cert.wt_line.amount, 3)

    def test_04_create_wt_cert_je_multi(self):
        """ Journal Entries to WT Certs """
        invoice = self._create_invoice(
            False, self.misc_journal.id, "entry", self.wt_account
        )
        self.assertEqual(invoice.state, "draft")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        invoice2 = invoice.copy()
        self.assertEqual(invoice2.state, "draft")
        # Create WT Cert from Journal Entry's Action Wizard
        ctx = {
            "active_ids": [invoice.id, invoice2.id],
            "active_model": "account.move",
        }
        res = self.wt_cert.with_context(ctx).action_create_withholding_tax_cert()
        view = self.env["ir.ui.view"].browse(res["view_id"]).xml_id
        # Error when create WT Cert with draft invoice
        with self.assertRaises(UserError):
            with Form(
                self.env[res["res_model"]].with_context(res["context"]), view=view
            ) as f:
                f.income_tax_form = "pnd3"
                f.wt_cert_income_type = "1"
            wizard = f.save()
        invoice2.action_post()
        with Form(
            self.env[res["res_model"]].with_context(res["context"]), view=view
        ) as f:
            f.income_tax_form = "pnd3"
            f.wt_cert_income_type = "1"
        wizard = f.save()
        wizard.write({"wt_account_ids": [self.wt_account.id]})
        res = wizard.create_wt_cert_multi()
        certs = self.wt_cert.search(res["domain"])
        self.assertEqual(len(certs), 2)
        for cert in certs:
            self.assertEqual(cert.wt_line.amount, 3)
