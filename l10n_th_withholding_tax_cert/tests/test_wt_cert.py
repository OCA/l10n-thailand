# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import tools
from odoo.exceptions import UserError
from odoo.modules.module import get_resource_path
from odoo.tests.common import Form, SavepointCase


class TestWTCert(SavepointCase):
    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(
            cls.cr,
            module,
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._load("account", "test", "account_minimal_test.xml")
        cls._load(
            "l10n_th_withholding_tax", "tests", "account_withholding_tax_test.xml"
        )
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.wt_cert = cls.env["withholding.tax.cert"]
        cls.wt_account = cls.browse_ref(
            cls, "l10n_th_withholding_tax.withholding_income_tax_account"
        )

    def _create_invoice(self, partner_id, journal_id, invoice_type, wt_account=False):
        a_expense = self.browse_ref("account.a_expense")
        bank_usd = self.browse_ref("account.usd_bnk")
        invoice_dict = {
            "name": "Test Supplier Invoice WT",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "type": invoice_type,
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
                                "account_id": bank_usd.id,
                                "partner_id": self.partner_1.id,
                                "name": "Test line credit",
                                "credit": 97.00,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": a_expense.id,
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
                                "account_id": a_expense.id,
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
        bank_journal = self.browse_ref("account.bank_journal")
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        view_id = "account.view_account_payment_invoice_form"
        with Form(self.account_payment.with_context(ctx), view=view_id) as f:
            f.journal_id = bank_journal
            f.amount = 97.0  # To withhold 3.0
            f.payment_difference_handling = "reconcile"
            f.writeoff_account_id = self.wt_account
            f.writeoff_label = "Withhold 3%"
        payment = f.save()
        payment.post()
        return payment

    def test_01_create_wt_cert_payment(self):
        """ Payment to WT Cert """
        expenses_journal = self.browse_ref("account.expenses_journal")
        invoice = self._create_invoice(
            self.partner_1.id, expenses_journal.id, "in_invoice"
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
        # get 1 line because compute 2 times
        cert.wt_line = cert.wt_line[0]
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
        misc_journal = self.browse_ref("account.miscellaneous_journal")
        invoice = self._create_invoice(False, misc_journal.id, "entry", self.wt_account)
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
        expenses_journal = self.browse_ref("account.expenses_journal")
        invoice = self._create_invoice(
            self.partner_1.id, expenses_journal.id, "in_invoice"
        )
        invoice2 = invoice.copy()
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
        misc_journal = self.browse_ref("account.miscellaneous_journal")
        invoice = self._create_invoice(False, misc_journal.id, "entry", self.wt_account)
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
