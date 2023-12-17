# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SavepointCase


class TestCompanyNoVatCosmetic(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.employee_1 = cls.env.ref("hr.employee_admin")
        cls.product_1 = cls.env.ref("product.product_product_4")
        cls.expenses = cls.env.ref("account.data_account_type_expenses")
        cls.expense_account = cls.env["account.account"].search(
            [
                ("user_type_id", "=", cls.expenses.id),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )
        cls.expenses_journal = cls.env["account.journal"].search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", cls.env.user.company_id.id),
            ],
            limit=1,
        )

    def test_01_purchase_cosmetic_vat(self):
        """If compnay novat=True, costmatic vat = 15%.
        When apply cosmetic_vat, price_subtotal will increase with vat
        and cosmetic_tax will be calculated"""
        self.env.company.novat = True
        po_line = {
            "product_id": self.product_1.id,
            "product_qty": 1.0,
            "price_unit": 100,
        }
        purchase = self.env["purchase.order"].create(
            {
                "name": "Test Purchase Cosmetic VAT",
                "partner_id": self.partner_1.id,
                "order_line": [(0, 0, po_line)],
            }
        )
        purchase._onchange_cosmetic_vat()
        self.assertTrue(purchase.cosmetic_vat)
        self.assertEqual(purchase.order_line[0].price_unit, 100)
        self.assertEqual(purchase.cosmetic_tax, 0)
        # Apply cosmetic vat
        purchase.apply_cosmetic_vat()
        self.assertEqual(purchase.order_line[0].price_unit, 115)
        self.assertEqual(purchase.cosmetic_tax, 15)
        # Remove cosmetic vat on line
        purchase.order_line.remove_cosmetic_vat()
        self.assertEqual(purchase.order_line[0].price_unit, 100)
        self.assertEqual(purchase.cosmetic_tax, 0)

    def test_02_invoice_cosmetic_vat(self):
        """If compnay novat=True, costmatic vat = 15%.
        When apply cosmetic_vat, price_subtotal will increase with vat
        and cosmetic_tax will be calculated"""
        self.env.company.novat = True
        inv_line = {
            "quantity": 1.0,
            "account_id": self.expense_account.id,
            "name": "Advice",
            "price_unit": 100,
        }
        invoice = self.env["account.move"].create(
            {
                "name": "Test Invoice Cosmetic VAT",
                "partner_id": self.partner_1.id,
                "journal_id": self.expenses_journal.id,
                "move_type": "in_invoice",
                "invoice_line_ids": [(0, 0, inv_line)],
            }
        )
        invoice._onchange_cosmetic_vat()
        self.assertTrue(invoice.cosmetic_vat)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 100)
        self.assertEqual(invoice.cosmetic_tax, 0)
        # Apply cosmetic vat
        invoice.apply_cosmetic_vat()
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 115)
        self.assertEqual(invoice.cosmetic_tax, 15)
        # Remove cosmetic vat on line
        invoice.invoice_line_ids.remove_cosmetic_vat()
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 100)
        self.assertEqual(invoice.cosmetic_tax, 0)

    def test_03_expense_cosmetic_vat(self):
        """If compnay novat=True, costmatic vat = 15%.
        When apply cosmetic_vat, price_subtotal will increase with vat
        and cosmetic_tax will be calculated"""
        self.env.company.novat = True
        ex_line = {
            "employee_id": self.employee_1.id,
            "name": "Test Expense Cosmetic VAT",
            "product_id": self.product_1.id,
            "quantity": 1.0,
            "unit_amount": 100,
        }
        expense = self.env["hr.expense.sheet"].create(
            {
                "name": "Test Expense Cosmetic VAT",
                "employee_id": self.employee_1.id,
                "expense_line_ids": [(0, 0, ex_line)],
            }
        )
        expense._onchange_cosmetic_vat()
        self.assertTrue(expense.cosmetic_vat)
        self.assertEqual(expense.expense_line_ids[0].unit_amount, 100)
        self.assertEqual(expense.cosmetic_tax, 0)
        # Apply cosmetic vat
        expense.apply_cosmetic_vat()
        self.assertEqual(expense.expense_line_ids[0].unit_amount, 115)
        self.assertEqual(expense.cosmetic_tax, 15)
        # Remove cosmetic vat on line
        expense.expense_line_ids.remove_cosmetic_vat()
        self.assertEqual(expense.expense_line_ids[0].unit_amount, 100)
        self.assertEqual(expense.cosmetic_tax, 0)
