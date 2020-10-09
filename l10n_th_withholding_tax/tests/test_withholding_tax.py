# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import tools
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tests.common import Form, SavepointCase


class TestWithholdingTax(SavepointCase):
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
        cls._load(
            "l10n_th_withholding_tax", "tests", "account_withholding_tax_test.xml"
        )
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.product_1 = cls.env.ref("product.product_product_4")
        cls.account_move = cls.env["account.move"]
        cls.account_payment = cls.env["account.payment"]
        cls.wt_account = cls.browse_ref(
            cls, "l10n_th_withholding_tax.account_withholding_tax_data"
        )
        cls.a_expense = cls.browse_ref(cls, "account.a_expense")
        cls.expenses_journal = cls.browse_ref(cls, "account.expenses_journal")

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
            "type": invoice_type,
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
        """ Create payment with withholding tax"""
        price_unit = 100.0
        with self.assertRaises(ValidationError):
            self.wt_account.write({"account_id": self.a_expense.id})

        invoice_id = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.a_expense.id,
            price_unit,
        )
        self.assertFalse(invoice_id.invoice_line_ids.wt_tax_id)
        invoice_id.invoice_line_ids.write({"wt_tax_id": self.wt_account.id})
        self.assertTrue(invoice_id.invoice_line_ids.wt_tax_id)
        invoice_id.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice_id.id],
            "active_id": invoice_id.id,
            "active_model": "account.move",
        }
        view_id = "account.view_account_payment_invoice_form"
        with Form(self.account_payment.with_context(ctx), view=view_id) as f:
            payment = f.save()
        self.assertEqual(
            payment.writeoff_account_id,
            invoice_id.invoice_line_ids.wt_tax_id.account_id,
        )
        self.assertEqual(payment.payment_difference, -(price_unit * 0.03))
        self.assertEqual(payment.writeoff_label, "Withholding Tax 3%")
        payment.post()
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, price_unit * 0.97)

    def test_02_create_payment_withholding_tax_product(self):
        """ Create payment with withholding tax from product"""
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wt_account.id, vendor=True
        )
        invoice_id = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.a_expense.id,
            price_unit,
            product_id.id,
        )
        wt_tax_id = invoice_id.invoice_line_ids.wt_tax_id
        self.assertTrue(wt_tax_id)
        self.assertEqual(wt_tax_id.account_id, self.wt_account.account_id)
        invoice_id.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice_id.id],
            "active_id": invoice_id.id,
            "active_model": "account.move",
        }
        view_id = "account.view_account_payment_invoice_form"
        with Form(self.account_payment.with_context(ctx), view=view_id) as f:
            payment = f.save()
        self.assertEqual(
            payment.writeoff_account_id,
            invoice_id.invoice_line_ids.wt_tax_id.account_id,
        )
        self.assertEqual(payment.payment_difference, -(price_unit * 0.03))
        self.assertEqual(payment.writeoff_label, "Withholding Tax 3%")
        payment.post()
        self.assertEqual(payment.state, "posted")
        self.assertEqual(payment.amount, price_unit * 0.97)

    def test_03_withholding_tax_customer_invoice(self):
        """ Test Case Withholding Tax from customer invoice"""
        sales_journal = self.browse_ref("account.sales_journal")
        a_sale = self.browse_ref("account.a_sale")
        price_unit = 100.0
        product_id = self._config_product_withholding_tax(
            self.product_1, self.wt_account.id, customer=True
        )
        invoice_id = self._create_invoice(
            self.partner_1.id,
            sales_journal.id,
            "out_invoice",
            a_sale.id,
            price_unit,
            product_id.id,
        )
        wt_tax_id = invoice_id.invoice_line_ids.wt_tax_id
        self.assertTrue(wt_tax_id)
        self.assertEqual(wt_tax_id.account_id, self.wt_account.account_id)
        invoice_id.action_post()
