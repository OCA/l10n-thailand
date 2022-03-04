# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import common
from odoo.tests.common import Form


class TestHrExpenseWithholdingTax(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.current_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.product_1 = cls.env.ref("product.product_product_4")
        cls.current_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.register_view_id = "account.view_account_payment_register_form"
        cls.account_payment_register = cls.env["account.payment.register"]
        cls.account_account = cls.env["account.account"]
        cls.account_journal = cls.env["account.journal"]
        cls.account_wht = cls.env["account.withholding.tax"]
        cls.expense = cls.env["hr.expense"]

        cls.journal_bank = cls.account_journal.search([("type", "=", "bank")], limit=1)
        cls.wht_account = cls.account_account.create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "user_type_id": cls.current_asset.id,
                "wht_account": True,
            }
        )
        cls.wht_1 = cls.account_wht.create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.wht_account.id,
                "amount": 1,
            }
        )
        employee_home = cls.env["res.partner"].create({"name": "Employee Home Address"})
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Employee A", "address_home_id": employee_home.id}
        )
        # Create expense 1,000
        cls.expense_sheet = cls._create_expense_sheet(
            cls, "Buy service 1,000", cls.employee, cls.product_1, 1000.0
        )
        # Create expense wht cert 1,000
        cls.expense_sheet_wht_cert = cls._create_expense_sheet(
            cls, "Buy service 1,000", cls.employee, cls.product_1, 1000.0, cls.wht_1
        )

    def _create_expense(
        self,
        description,
        employee,
        product,
        amount,
        wht_tax_id=False,
        payment_mode="own_account",
    ):
        with Form(self.expense) as expense:
            expense.name = description
            expense.employee_id = employee
            expense.product_id = product
            expense.unit_amount = amount
            expense.payment_mode = payment_mode
            if wht_tax_id:
                expense.wht_tax_id = wht_tax_id
        expense = expense.save()
        expense.tax_ids = False  # Test no vat
        return expense

    def _create_expense_sheet(
        self, description, employee, product, amount, wht_tax_id=False
    ):
        expense = self._create_expense(
            self, description, employee, product, amount, wht_tax_id
        )
        # Add expense to expense sheet
        expense_sheet = self.env["hr.expense.sheet"].create(
            {
                "name": description,
                "employee_id": expense.employee_id.id,
                "expense_line_ids": [(6, 0, [expense.id])],
            }
        )
        return expense_sheet

    def _register_payment(self, move_id):
        ctx = {
            "active_ids": [move_id.id],
            "active_id": move_id.id,
            "active_model": "account.move",
        }
        PaymentWizard = self.env["account.payment.register"]
        with Form(PaymentWizard.with_context(**ctx)) as f:
            f.journal_id = self.journal_bank
            f.payment_date = fields.Date.today()
        payment_wizard = f.save()
        return payment_wizard

    def test_01_expense_wht_cert(self):
        """Test Expense Withholding Tax"""
        self.assertTrue(self.expense_sheet_wht_cert.expense_line_ids.wht_tax_id)
        self.expense_sheet_wht_cert.action_submit_sheet()
        self.expense_sheet_wht_cert.approve_expense_sheets()
        self.expense_sheet_wht_cert.action_sheet_move_create()
        self.assertEqual(self.expense_sheet_wht_cert.state, "post")
        payment_wizard = self._register_payment(
            self.expense_sheet_wht_cert.account_move_id
        )
        self.assertEqual(
            payment_wizard.amount, 1000.0 - (1000.0 * (self.wht_1.amount / 100))
        )
        payment_wizard.action_create_payments()
        self.assertEqual(self.expense_sheet_wht_cert.state, "done")

    def test_02_expense_no_wht_cert(self):
        """Test Expense not Withholding Tax"""
        self.assertFalse(self.expense_sheet.expense_line_ids.wht_tax_id)
        self.expense_sheet.action_submit_sheet()
        self.expense_sheet.approve_expense_sheets()
        self.expense_sheet.action_sheet_move_create()
        self.assertEqual(self.expense_sheet.state, "post")
        payment_wizard = self._register_payment(self.expense_sheet.account_move_id)
        self.assertEqual(payment_wizard.amount, 1000.0)
        payment_wizard.action_create_payments()
        self.assertEqual(self.expense_sheet.state, "done")
