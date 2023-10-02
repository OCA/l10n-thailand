# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountEntry(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_expense = cls.env["account.account"].create(
            {
                "code": "NC1113",
                "name": "HR Expense - Test Purchase Account",
                "account_type": "expense",
            }
        )
        cls.input_vat_acct = cls.env["account.account"].create(
            {"name": "V7", "code": "V7", "account_type": "liability_current"}
        )
        cls.tax_group_vat = cls.env["account.tax.group"].create({"name": "VAT"})
        cls.input_vat_include = cls.env["account.tax"].create(
            {
                "name": "V7",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 7.0,
                "tax_group_id": cls.tax_group_vat.id,
                "price_include": True,
                "tax_exigibility": "on_invoice",
                "invoice_repartition_line_ids": [
                    Command.create(
                        {"factor_percent": 100.0, "repartition_type": "base"}
                    ),
                    Command.create(
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.input_vat_acct.id,
                        }
                    ),
                ],
            }
        )
        cls.product_expense = cls.env["product.product"].create(
            {
                "name": "Delivered at cost",
                "standard_price": 700,
                "list_price": 700,
                "type": "consu",
                "supplier_taxes_id": [Command.set([cls.input_vat_include.id])],
                "default_code": "CONSU-DELI-COST",
                "taxes_id": False,
                "property_account_expense_id": cls.account_expense.id,
            }
        )
        # Create new employee
        partner = cls.env["res.partner"].create({"name": "Test Employee"})
        cls.employee1 = cls.env["hr.employee"].create(
            {"name": "Test Employee", "address_home_id": partner.id}
        )

    def test_expense_tax_invoice(self):
        """hr.expense's reference & date is used as Tax Invoice and Date
        if not filled, do not allow journal entry posting
        """
        expense = self.env["hr.expense.sheet"].create(
            {"name": "Expense for John Smith", "employee_id": self.employee1.id}
        )
        expense_line = self.env["hr.expense"].create(
            {
                "name": "Car Travel Expenses",
                "employee_id": self.employee1.id,
                "product_id": self.product_expense.id,
                "total_amount": 700.00,
                "tax_ids": [Command.set([self.input_vat_include.id])],
                "sheet_id": expense.id,
            }
        )
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        with self.assertRaises(
            UserError, msg="Please fill in tax invoice and tax date"
        ):
            expense.action_sheet_move_create()
        expense_line.write({"reference": "TAXINV-001"})
        expense.action_sheet_move_create()
        self.assertEqual(expense.state, "post")
