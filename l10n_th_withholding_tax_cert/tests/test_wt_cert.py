# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import tools
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
            "l10n_th_withholding_tax_cert", "tests", "account_withholding_tax_test.xml"
        )
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.wt_cert = cls.env["withholding.tax.cert"]
        cls.wt_cert_wizard = cls.env["create.withholding.tax.cert"]

    def _create_invoice(self, partner_id, journal_id, invoice_type, wt_account=False):
        a_expense = self.browse_ref("account.a_expense")
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
                                "name": "Test line credit",
                                "credit": 100.00,
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
        invoice_id = self.account_move.create(invoice_dict)
        return invoice_id

    def test_01_create_wt_cert_payment(self):
        """ Payment to WT Cert """
        bank_journal = self.browse_ref("account.bank_journal")
        expenses_journal = self.browse_ref("account.expenses_journal")
        wt_account = self.browse_ref(
            "l10n_th_withholding_tax_cert.withholding_income_tax_account"
        )
        invoice_id = self._create_invoice(
            self.partner_1.id, expenses_journal.id, "in_invoice"
        )
        invoice_id.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice_id.id],
            "active_id": invoice_id.id,
            "active_model": "account.move",
        }
        view_id = "account.view_account_payment_invoice_form"
        with Form(self.account_payment.with_context(ctx), view=view_id) as f:
            f.journal_id = bank_journal
            f.amount = 97.0  # To withhold 3.0
            f.payment_difference_handling = "reconcile"
            f.writeoff_account_id = wt_account
            f.writeoff_label = "Withhold 3%"
        payment = f.save()
        payment.post()
        self.assertEqual(payment.state, "posted")
        # Create WT Cert from Payment's Action Wizard
        ctx = {
            "active_id": payment.id,
            "active_ids": [payment.id],
            "active_model": "account.payment",
        }
        f = Form(self.wt_cert_wizard.with_context(ctx))
        wizard = f.save()
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"default_income_tax_form": "pnd3", "wt_cert_income_type": "1"})
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
        ctx_cert.update({"default_income_tax_form": "pnd3", "wt_cert_income_type": "1"})
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
        wt_account = self.browse_ref(
            "l10n_th_withholding_tax_cert.withholding_income_tax_account"
        )
        misc_journal = self.browse_ref("account.miscellaneous_journal")
        invoice_id = self._create_invoice(False, misc_journal.id, "entry", wt_account)
        invoice_id.action_post()
        # Create WT Cert from Journal Entry's Action Wizard
        ctx = {
            "active_id": invoice_id.id,
            "active_ids": [invoice_id.id],
            "active_model": "account.move",
        }
        f = Form(self.wt_cert_wizard.with_context(ctx))
        wizard = f.save()
        wizard.write({"wt_account_ids": invoice_id.line_ids.mapped("account_id")})
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"default_income_tax_form": "pnd3", "wt_cert_income_type": "1"})
        with Form(self.wt_cert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        wt_cert = f.save()
        self.assertEqual(wt_cert.supplier_partner_id, self.partner_1)
        invoice_id.button_wt_certs()
