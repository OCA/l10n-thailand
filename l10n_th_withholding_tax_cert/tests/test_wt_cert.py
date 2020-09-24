# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import Form, SingleTransactionCase


class TestWTCert(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestWTCert, cls).setUpClass()
        # Accounts
        type_asset = cls.env.ref("account.data_account_type_current_assets")
        expense_account = cls.env.ref("account.data_account_type_expenses")
        receivable_account = cls.env.ref("account.data_account_type_receivable")
        payable_account = cls.env.ref("account.data_account_type_payable")
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.account_journal = cls.env["account.journal"]
        cls.account_account = cls.env["account.account"]
        cls.wt_cert = cls.env["withholding.tax.cert"]
        cls.wt_cert_wizard = cls.env["create.withholding.tax.cert"]
        cls.wt_account_payable = cls.account_account.create(
            {
                "name": "SUP_WT_3",
                "code": "SUPWT3",
                "user_type_id": type_asset.id,
                "wt_account": True,
            }
        )
        # Journals
        cls.journal_bank = cls.account_journal.create(
            {"name": "Bank", "type": "bank", "code": "BNK67"}
        )
        cls.journal_purchase = cls.account_journal.search(
            [("type", "=", "purchase")], limit=1
        )
        if not cls.journal_purchase:
            cls.journal_purchase = cls.account_journal.create(
                {"name": "Purchase 1", "type": "purchase", "code": "PO"}
            )
        cls.journal_misc = cls.account_journal.search(
            [("type", "=", "general")], limit=1
        )
        if not cls.journal_misc:
            cls.journal_misc = cls.account_journal.create(
                {"name": "Misc 1", "type": "general", "code": "MISC"}
            )
        # Prepare Supplier Invoices
        cls.expense_account = cls.account_account.search(
            [("user_type_id", "=", expense_account.id)], limit=1,
        )
        if not cls.expense_account:
            cls.expense_account = cls.account_account.create(
                {
                    "code": 19292,
                    "name": "Expense Account",
                    "user_type_id": expense_account.id,
                }
            )
        cls.account_receivable = cls.account_account.search(
            [("user_type_id", "=", receivable_account.id)], limit=1,
        )
        if not cls.account_receivable:
            cls.account_receivable = cls.account_account.create(
                {
                    "code": 11111990,
                    "name": "Receivable Test",
                    "user_type_id": receivable_account.id,
                    "reconcile": True,
                }
            )
        cls.account_payable = cls.account_account.search(
            [("user_type_id", "=", payable_account.id)], limit=1,
        )
        if not cls.account_payable:
            cls.account_payable = cls.account_account.create(
                {
                    "code": 21111990,
                    "name": "Payable Test",
                    "user_type_id": payable_account.id,
                    "reconcile": True,
                }
            )
        if not cls.partner_1.property_account_receivable_id:
            cls.partner_1.write(
                {
                    "property_account_receivable_id": cls.account_receivable.id,
                    "property_account_payable_id": cls.account_payable.id,
                }
            )

    def _create_invoice(self, partner_id, journal_id, invoice_type):
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
                                "account_id": self.wt_account_payable.id,
                                "partner_id": self.partner_1.id,
                                "name": "Test line credit",
                                "credit": 100.00,
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
        invoice_id = self.account_move.create(invoice_dict)
        return invoice_id

    def test_01_create_wt_cert_payment(self):
        """ Payment to WT Cert """
        invoice_id = self._create_invoice(
            self.partner_1.id, self.journal_purchase.id, "in_invoice"
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
            f.journal_id = self.journal_bank
            f.amount = 97.0  # To withhold 3.0
            f.payment_difference_handling = "reconcile"
            f.writeoff_account_id = self.wt_account_payable
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
        self.assertEqual(cert.state, "draft")
        self.assertRecordValues(cert.wt_line, [{"amount": 3.0}])
        payment.button_wt_certs()
        cert.action_done()
        self.assertEqual(cert.state, "done")
        # substitute WT Cert
        wizard.write({"substitute": True, "wt_cert_id": cert})
        res = wizard.create_wt_cert()
        self.assertEqual(cert.state, "cancel")

    def test_02_create_wt_cert_je(self):
        """ Journal Entry to WT Cert """
        invoice_id = self._create_invoice(False, self.journal_misc.id, "entry")
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
