# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import Form, SingleTransactionCase


class TestWTCert(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestWTCert, cls).setUpClass()
        # Accounts
        type_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.wt_account_payable = cls.env["account.account"].create(
            {
                "name": "SUP_WT_3",
                "code": "SUPWT3",
                "user_type_id": type_asset.id,
                "wt_account": True,
            }
        )
        # Journals
        cls.journal_bank = cls.env["account.journal"].create(
            {"name": "Bank", "type": "bank", "code": "BNK67"}
        )
        cls.journal_purchase = cls.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )
        cls.journal_misc = cls.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        )
        # Prepare Supplier Invoices
        cls.expense_account = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_expenses").id,
                )
            ],
            limit=1,
        )

    def _create_invoice(self, partner_id, journal_id, invoice_type):
        invoice_dict = {
            "name": "Test Supplier Invoice WT",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "type": invoice_type,
        }
        if type == "entry":
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
        return invoice_dict

    def test_01_create_wt_cert_payment(self):
        """ Payment to WT Cert """
        # User have not filled in Tax Invoice / Date in account_invoice_tax
        invoice_dict = self._create_invoice(
            self.partner_1.id, self.journal_purchase.id, "in_invoice"
        )
        supplier_invoice_wt = self.account_move.create(invoice_dict)
        supplier_invoice_wt.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [supplier_invoice_wt.id],
            "active_id": supplier_invoice_wt.id,
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
        f = Form(self.env["create.withholding.tax.cert"].with_context(ctx))
        wizard = f.save()
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"default_income_tax_form": "pnd3", "wt_cert_income_type": "1"})
        WTCert = self.env["withholding.tax.cert"]
        with Form(WTCert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        cert = f.save()
        self.assertRecordValues(cert.wt_line, [{"amount": 3.0}])

    def test_02_create_wt_cert_je(self):
        """ Journal Entry to WT Cert """
        invoice_dict = self._create_invoice(False, self.journal_misc.id, "entry")
        move_wt = self.account_move.create(invoice_dict)
        move_wt.action_post()
        # Create WT Cert from Journal Entry's Action Wizard
        ctx = {
            "active_id": move_wt.id,
            "active_ids": [move_wt.id],
            "active_model": "account.move",
        }
        f = Form(self.env["create.withholding.tax.cert"].with_context(ctx))
        wizard = f.save()
        res = wizard.create_wt_cert()
        # New WT Cert
        ctx_cert = res.get("context")
        ctx_cert.update({"default_income_tax_form": "pnd3", "wt_cert_income_type": "1"})
        WTCert = self.env["withholding.tax.cert"]
        with Form(WTCert.with_context(ctx_cert)) as f:
            f.income_tax_form = "pnd3"
        wt_cert = f.save()
        self.assertEqual(wt_cert.supplier_partner_id, self.partner_1)
        move_wt.button_wt_certs()
