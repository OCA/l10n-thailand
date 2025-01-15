# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("-at_install", "post_install")
class TestAccountEntry(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env.ref("base.res_partner_12")

    def test_expense_tax_invoice(self):
        """hr.expense's tax_number & tax_date is used as Tax Invoice and Date
        if not filled, do not allow bill posting
        """
        expense_sheet = self.create_expense_report(
            {
                "name": "Expense for John Smith",
                "expense_line_ids": [
                    Command.create(
                        {
                            "name": "PA 2*800 + 15%",  # Taxes are included
                            "employee_id": self.expense_employee.id,
                            # Test with a specific account override
                            "account_id": self.expense_account.id,
                            "product_id": self.product_a.id,
                            "quantity": 2,
                            "payment_mode": "own_account",
                            "company_id": self.company_data["company"].id,
                            "date": "2021-10-11",
                            "analytic_distribution": {self.analytic_account_1.id: 100},
                            "total_amount_currency": 1000.00,
                            "tax_ids": [Command.set(self.tax_purchase_a.ids)],
                        }
                    )
                ],
            }
        )
        expense_sheet.action_submit_sheet()
        expense_sheet.action_approve_expense_sheets()
        with self.assertRaises(
            UserError, msg="Please fill in tax invoice and tax date"
        ):
            expense_sheet.action_sheet_move_post()
        expense_sheet.expense_line_ids.write(
            {
                "tax_number": "TAXINV-001",
                "tax_date": "2021-10-11",
                "bill_partner_id": self.partner1.id,
            }
        )
        expense_sheet.action_sheet_move_post()
        self.assertEqual(expense_sheet.state, "post")
