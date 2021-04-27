# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.tests.common import Form, SavepointCase


class TestCompanyNoVat(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env.ref("base.res_partner_12")
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
        cls.wt_1 = cls.account_wtax.create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.wt_account.id,
                "amount": 1,
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
        tax=False,
    ):
        invoice_dict = {
            "name": "Test Supplier Invoice WT",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "move_type": invoice_type,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "quantity": 1.0,
                        "account_id": line_account_id,
                        "name": "Advice",
                        "price_unit": price_unit or 0.0,
                    },
                )
            ],
        }
        if tax:
            invoice_dict["invoice_line_ids"][0][2]["tax_ids"] = [(4, tax.id)]
        invoice_id = self.account_move.create(invoice_dict)
        return invoice_id

    def test_01_company_novat(self):
        """ If compnay novat=True, document can't select taxes """
        self.env.company.novat = True
        price_unit = 100.0
        tax = self.env["account.tax"].search([])[:1]
        # Create invoice with Tax
        # Taxes not allowed for Non-VAT registered company
        with self.assertRaises(UserError):
            invoice = self._create_invoice(
                self.partner_1.id,
                self.expenses_journal.id,
                "in_invoice",
                self.expense_account.id,
                price_unit,
                tax=tax,
            )
        # Create invoice first, then assign tax later
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        # Write tax
        # Taxes not allowed for Non-VAT registered company
        with self.assertRaises(UserError):
            invoice.invoice_line_ids.write({"tax_ids": [(4, tax.id)]})

    def test_02_company_novat_vendor_novat(self):
        """ Company No-VAT, and Vendor No-VAT -> WHT based on full amount """
        self.env.company.novat = True
        self.partner_1.novat = True
        self.env.company.account_purchase_tax_id.amount = 7
        price_unit = 107.0  # included vat amount
        # Create invoice for parnter No-VAT
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        # Assign WT
        invoice.invoice_line_ids.write({"wt_tax_id": self.wt_1.id})
        # partner No-VAT, no special wtvat
        wtvat = invoice.invoice_line_ids[:1].wtvat
        self.assertEqual(wtvat, 0)
        invoice.invoice_date = invoice.date
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
        # Based on untaxed amount = 107, the WHT1% amount is 1.07
        self.assertEqual(register_payment.payment_difference, 1.07)

    def test_03_company_novat_vendor_vat(self):
        """ Company No-VAT, but vendor VAT, we want to withhold on untaxed amount """
        self.env.company.novat = True
        self.partner_1.novat = False
        self.env.company.account_purchase_tax_id.amount = 7
        # self.env["account.tax"].write({"amount": 7})  # Set VAT = 7% for test
        price_unit = 107.0  # included vat amount
        # Create invoice for parnter No-VAT
        invoice = self._create_invoice(
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        # Assign WT
        invoice.invoice_line_ids.write({"wt_tax_id": self.wt_1.id})
        # partner No-VAT, no special wtvat
        wtvat = invoice.invoice_line_ids[:1].wtvat
        self.assertEqual(wtvat, 7)
        invoice.invoice_date = invoice.date
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
        # Based on untaxed amount = 100, the WHT1% amount is 1.07
        self.assertEqual(register_payment.payment_difference, 1.00)
