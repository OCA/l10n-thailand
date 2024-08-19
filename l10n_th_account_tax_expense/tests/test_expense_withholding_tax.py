# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged("post_install", "-at_install")
class TestHrExpenseWithholdingTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_travel = cls.env.ref(
            "hr_expense.expense_product_travel_accommodation"
        )
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
                "account_type": "asset_current",
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
        cls.partner1 = cls.env.ref("base.res_partner_1")
        # Create account advance
        advance_account = cls.env["account.account"].create(
            {
                "code": "154000",
                "name": "Employee Advance",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )

        cls.emp_advance = cls.env.ref("hr_expense_advance_clearing.product_emp_advance")
        cls.emp_advance.property_account_expense_id = advance_account
        # Create expense 1,000
        cls.expense_sheet = cls._create_expense_sheet(
            cls, "Buy service 1,000", cls.employee, cls.product_travel, 1000.0
        )
        # Create expense wht cert 1,000
        cls.expense_sheet_wht_cert = cls._create_expense_sheet(
            cls,
            "Buy service 1,000",
            cls.employee,
            cls.product_travel,
            1000.0,
            cls.wht_1,
        )
        # Create advance expense 1,000
        cls.advance = cls._create_expense_sheet(
            cls, "Advance 1,000", cls.employee, cls.emp_advance, 1000.0, advance=True
        )
        # # Create clearing expense 800
        cls.clearing_less = cls._create_expense_sheet(
            cls, "Buy service 800", cls.employee, cls.product_travel, 800.0, cls.wht_1
        )
        # Create clearing expense 1,200
        cls.clearing_more = cls._create_expense_sheet(
            cls,
            "Buy service 1,200",
            cls.employee,
            cls.product_travel,
            1200.0,
            cls.wht_1,
        )

    def _create_expense(
        self,
        description,
        employee,
        product,
        amount,
        wht_tax_id=False,
        advance=False,
    ):
        with Form(self.expense.with_context(default_advance=advance)) as expense:
            expense.name = description
            expense.employee_id = employee
            if not advance:
                expense.product_id = product
            expense.total_amount = amount
            if wht_tax_id:
                expense.wht_tax_id = wht_tax_id
                expense.bill_partner_id = self.partner1
        expense = expense.save()
        expense.tax_ids = False  # Test no vat
        return expense

    def _create_expense_sheet(
        self, description, employee, product, amount, wht_tax_id=False, advance=False
    ):
        expense = self._create_expense(
            self, description, employee, product, amount, wht_tax_id, advance
        )
        # Add expense to expense sheet
        expense_sheet = self.env["hr.expense.sheet"].create(
            {
                "name": description,
                "employee_id": expense.employee_id.id,
                "expense_line_ids": [Command.set([expense.id])],
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

    def test_03_advance_clearing_more_wht_cert(self):
        """Test Clearing with Witholding Tax > Advance"""
        # ------------------ Advance --------------------------
        self.advance.action_submit_sheet()
        self.advance.approve_expense_sheets()
        self.advance.action_sheet_move_create()
        self.assertEqual(self.advance.clearing_residual, 1000.0)
        payment_wizard = self._register_payment(self.advance.account_move_id)
        payment_wizard.action_create_payments()
        self.assertEqual(self.advance.state, "done")
        # ------------------ Clearing --------------------------
        # Clear this with previous advance
        self.clearing_more.advance_sheet_id = self.advance
        self.assertEqual(self.clearing_more.advance_sheet_residual, 1000.0)
        self.clearing_more.action_submit_sheet()
        # Can create wht state done or post only
        with self.assertRaises(UserError):
            self.clearing_more.action_create_withholding_tax_entry()
        self.clearing_more.approve_expense_sheets()
        self.clearing_more.action_sheet_move_create()
        # clearing > advance, it will change state to post
        self.assertEqual(self.clearing_more.state, "post")
        # check context skip_wht_deduct when register payment with clearing
        register_payment = self.clearing_more.action_register_payment()
        self.assertTrue(register_payment["context"]["skip_wht_deduct"])
        self.assertTrue(self.clearing_more.need_wht_entry)
        self.assertFalse(self.clearing_more.wht_move_id)
        # Create withholding tax
        res = self.clearing_more.action_create_withholding_tax_entry()
        self.assertTrue(self.clearing_more.wht_move_id)
        self.assertEqual(self.clearing_more.wht_move_id.id, res["res_id"])
        # Open withholding tax
        res = self.clearing_more.action_open_wht_move()
        self.assertEqual(res["res_model"], "account.move")
        self.assertEqual(res["res_id"], self.clearing_more.wht_move_id.id)
        # it should not create duplicate withholding tax
        with self.assertRaises(UserError):
            self.clearing_more.action_create_withholding_tax_entry()
        # Post withholding tax
        self.assertEqual(self.clearing_more.wht_move_id.state, "draft")
        self.clearing_more.wht_move_id.action_post()
        self.assertEqual(self.clearing_more.wht_move_id.state, "posted")
        self.assertTrue(self.clearing_more.wht_move_id.has_wht)
        # it should not cancel clearing, if there are withholding tax
        with self.assertRaises(UserError):
            self.clearing_more.account_move_id.button_cancel()
        # cancel withholding tax first
        self.clearing_more.wht_move_id.button_draft()
        self.assertEqual(self.clearing_more.wht_move_id.state, "draft")
        self.clearing_more.wht_move_id.button_cancel()
        self.assertEqual(self.clearing_more.wht_move_id.state, "cancel")
        # cancel clearing move
        self.clearing_more.account_move_id.button_cancel()
        self.assertEqual(self.clearing_more.account_move_id.state, "cancel")

    def test_04_advance_clearing_less_wht_cert(self):
        """Test Clearing with Witholding Tax < Advance"""
        # ------------------ Advance --------------------------
        self.advance.action_submit_sheet()
        self.advance.approve_expense_sheets()
        self.advance.action_sheet_move_create()
        self.assertEqual(self.advance.clearing_residual, 1000.0)
        payment_wizard = self._register_payment(self.advance.account_move_id)
        payment_wizard.action_create_payments()
        self.assertEqual(self.advance.state, "done")
        # ------------------ Clearing --------------------------
        # Clear this with previous advance
        self.clearing_less.advance_sheet_id = self.advance
        self.assertEqual(self.clearing_less.advance_sheet_residual, 1000.0)
        self.clearing_less.action_submit_sheet()
        # Can create wht state done or post only
        with self.assertRaises(UserError):
            self.clearing_less.action_create_withholding_tax_entry()
        self.clearing_less.approve_expense_sheets()
        self.clearing_less.action_sheet_move_create()
        # clearing < advance, it will change state to done
        self.assertEqual(self.clearing_less.state, "done")
        # check context skip_wht_deduct when register payment with clearing
        register_payment = self.clearing_less.action_register_payment()
        self.assertTrue(register_payment["context"]["skip_wht_deduct"])
        self.assertTrue(self.clearing_less.need_wht_entry)
        self.assertFalse(self.clearing_less.wht_move_id)
        self.assertEqual(self.clearing_less.advance_sheet_residual, 200.0)
        # Create withholding tax
        res = self.clearing_less.action_create_withholding_tax_entry()
        self.assertTrue(self.clearing_less.wht_move_id)
        self.assertEqual(self.clearing_less.wht_move_id.id, res["res_id"])
        # Open withholding tax
        res = self.clearing_less.action_open_wht_move()
        self.assertEqual(res["res_model"], "account.move")
        self.assertEqual(res["res_id"], self.clearing_less.wht_move_id.id)
        # it should not create duplicate withholding tax
        with self.assertRaises(UserError):
            self.clearing_less.action_create_withholding_tax_entry()
        # Post withholding tax
        self.assertEqual(self.clearing_less.wht_move_id.state, "draft")
        self.clearing_less.wht_move_id.action_post()
        self.assertEqual(self.clearing_less.wht_move_id.state, "posted")
        self.assertTrue(self.clearing_less.wht_move_id.has_wht)
        self.assertEqual(self.clearing_less.advance_sheet_residual, 208.0)
        # it should not cancel clearing, if there are withholding tax
        with self.assertRaises(UserError):
            self.clearing_less.account_move_id.button_cancel()
        # cancel withholding tax first
        self.clearing_less.wht_move_id.button_draft()
        self.assertEqual(self.clearing_less.wht_move_id.state, "draft")
        self.clearing_less.wht_move_id.button_cancel()
        self.assertEqual(self.clearing_less.wht_move_id.state, "cancel")
        # cancel clearing move
        self.clearing_less.account_move_id.button_cancel()
        self.assertEqual(self.clearing_less.account_move_id.state, "cancel")
