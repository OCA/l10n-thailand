# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.exceptions import UserError

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


class TestAccountEntry(TestExpenseCommon):
    def setUp(self):
        super(TestAccountEntry, self).setUp()

        self.setUpAdditionalAccounts()

        self.product_expense = self.env["product.product"].create(
            {
                "name": "Delivered at cost",
                "standard_price": 700,
                "list_price": 700,
                "type": "consu",
                "supplier_taxes_id": [(6, 0, [self.tax.id])],
                "default_code": "CONSU-DELI-COST",
                "taxes_id": False,
                "property_account_expense_id": self.account_expense.id,
            }
        )

    def test_expense_tax_invoice(self):
        """hr.expense's reference & date is used as Tax Invoice and Date
        if not filled, do not allow journal entry posting
        """
        expense = self.env["hr.expense.sheet"].create(
            {"name": "Expense for John Smith", "employee_id": self.employee.id}
        )
        expense_line = self.env["hr.expense"].create(
            {
                "name": "Car Travel Expenses",
                "employee_id": self.employee.id,
                "product_id": self.product_expense.id,
                "unit_amount": 700.00,
                "tax_ids": [(6, 0, [self.tax.id])],
                "sheet_id": expense.id,
            }
        )
        expense_line._onchange_product_id()
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        with self.assertRaises(
            UserError, msg="Please fill in tax invoice and tax date"
        ):
            expense.action_sheet_move_create()
        expense_line.write({"reference": "TAXINV-001"})
        expense.action_sheet_move_create()
        self.assertEquals(
            expense.state, "post", "Expense is not in Waiting Payment state"
        )
