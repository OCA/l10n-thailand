# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("post_install", "-at_install")
class TestAccountEntry(TestExpenseCommon):
    def setUp(self):
        super().setUp()

        user_type_expense = self.env.ref("account.data_account_type_expenses")
        self.account_expense = self.env["account.account"].create(
            {
                "code": "NC1113",
                "name": "HR Expense - Test Purchase Account",
                "user_type_id": user_type_expense.id,
            }
        )
        type_current_liability = self.env.ref(
            "account.data_account_type_current_liabilities"
        )
        self.input_vat_acct = self.env["account.account"].create(
            {"name": "V7", "code": "V7", "user_type_id": type_current_liability.id}
        )
        self.tax_group_vat = self.env["account.tax.group"].create({"name": "VAT"})
        self.input_vat_include = self.env["account.tax"].create(
            {
                "name": "V7",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 7.0,
                "tax_group_id": self.tax_group_vat.id,
                "price_include": True,
                "tax_exigibility": "on_invoice",
                "invoice_repartition_line_ids": [
                    (0, 0, {"factor_percent": 100.0, "repartition_type": "base"}),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": self.input_vat_acct.id,
                        },
                    ),
                ],
            }
        )
        self.product_expense = self.env["product.product"].create(
            {
                "name": "Delivered at cost",
                "standard_price": 700,
                "list_price": 700,
                "type": "consu",
                "supplier_taxes_id": [(6, 0, [self.input_vat_include.id])],
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
            {"name": "Expense for John Smith", "employee_id": self.expense_employee.id}
        )
        expense_line = self.env["hr.expense"].create(
            {
                "name": "Car Travel Expenses",
                "employee_id": self.expense_employee.id,
                "product_id": self.product_expense.id,
                "unit_amount": 700.00,
                "tax_ids": [(6, 0, [self.input_vat_include.id])],
                "sheet_id": expense.id,
            }
        )
        expense_line._compute_from_product_id_company_id()
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        with self.assertRaises(
            UserError, msg="Please fill in tax invoice and tax date"
        ):
            expense.action_sheet_move_create()
        expense_line.write({"reference": "TAXINV-001"})
        expense.action_sheet_move_create()
        self.assertEqual(expense.state, "post")
