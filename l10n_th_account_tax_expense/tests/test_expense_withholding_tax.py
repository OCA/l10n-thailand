# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("-at_install", "post_install")
class TestHrExpenseWithholdingTax(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_travel = cls.env.ref(
            "hr_expense.expense_product_travel_accommodation"
        )
        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.account_payment_register = cls.env["account.payment.register"]
        cls.account_account = cls.env["account.account"]
        cls.account_wht = cls.env["account.withholding.tax"]
        cls.expense = cls.env["hr.expense"]

        cls.wht_account = cls.account_account.create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "account_type": "liability_current",
                "wht_account": True,
                "reconcile": True,
            }
        )
        cls.wht_1 = cls.account_wht.create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.wht_account.id,
                "amount": 1,
            }
        )

        # Create account advance
        cls.advance_account = cls.env["account.account"].create(
            {
                "code": "154000",
                "name": "Employee Advance",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )

        cls.emp_advance = cls.env.ref("hr_expense_advance_clearing.product_emp_advance")
        cls.emp_advance.property_account_expense_id = cls.advance_account
        # Create expense 1,000
        cls.expense_sheet = cls.create_expense_report(
            cls,
            {
                "name": "Buy service 1,000",
                "expense_line_ids": [
                    Command.create(
                        {
                            "name": "PA 1,000",  # Taxes are included
                            "employee_id": cls.expense_employee.id,
                            "product_id": cls.product_travel.id,
                            "quantity": 1,
                            "payment_mode": "own_account",
                            "company_id": cls.company_data["company"].id,
                            "date": "2021-10-11",
                            "total_amount_currency": 1000.00,
                            "tax_ids": False,
                        }
                    )
                ],
            },
        )
        # Create expense wht cert 1,000
        cls.expense_sheet_wht_cert = cls.create_expense_report(
            cls,
            {
                "name": "Buy service 1,000",
                "expense_line_ids": [
                    Command.create(
                        {
                            "name": "PA 1,000 (WHT)",
                            "employee_id": cls.expense_employee.id,
                            "product_id": cls.product_travel.id,
                            "quantity": 1,
                            "payment_mode": "own_account",
                            "company_id": cls.company_data["company"].id,
                            "date": "2021-10-11",
                            "total_amount_currency": 1000.00,
                            "wht_tax_id": cls.wht_1.id,
                            "bill_partner_id": cls.partner1.id,
                            "tax_ids": False,
                        }
                    )
                ],
            },
        )
        # Create advance expense 1,000
        cls.advance = cls.create_expense_report(
            cls,
            {
                "name": "Buy service 1,000",
                "advance": True,
                "expense_line_ids": [
                    Command.create(
                        {
                            "advance": True,
                            "name": "Advance 1,000",
                            "employee_id": cls.expense_employee.id,
                            "product_id": cls.emp_advance.id,
                            "quantity": 1,
                            "payment_mode": "own_account",
                            "company_id": cls.company_data["company"].id,
                            "date": "2021-10-11",
                            "total_amount_currency": 1000.00,
                            "tax_ids": False,
                        }
                    )
                ],
            },
        )
        # Create clearing expense 800
        cls.clearing_less = cls.create_expense_report(
            cls,
            {
                "name": "Buy service 800",
                "expense_line_ids": [
                    Command.create(
                        {
                            "name": "Clearing 800",
                            "employee_id": cls.expense_employee.id,
                            "product_id": cls.product_travel.id,
                            "quantity": 1,
                            "payment_mode": "own_account",
                            "company_id": cls.company_data["company"].id,
                            "date": "2021-10-11",
                            "total_amount_currency": 800.00,
                            "wht_tax_id": cls.wht_1.id,
                            "bill_partner_id": cls.partner1.id,
                            "tax_ids": False,
                        }
                    )
                ],
            },
        )

        # Create clearing expense 1,200
        cls.clearing_more = cls.create_expense_report(
            cls,
            {
                "name": "Buy service 1,200",
                "expense_line_ids": [
                    Command.create(
                        {
                            "name": "Clearing 1,200",
                            "employee_id": cls.expense_employee.id,
                            "product_id": cls.product_travel.id,
                            "quantity": 1,
                            "payment_mode": "own_account",
                            "company_id": cls.company_data["company"].id,
                            "date": "2021-10-11",
                            "total_amount_currency": 1200.00,
                            "wht_tax_id": cls.wht_1.id,
                            "bill_partner_id": cls.partner1.id,
                            "tax_ids": False,
                        }
                    )
                ],
            },
        )

    def _register_payment(self, move_id):
        wizard = (
            self.env["account.payment.register"]
            .with_context(
                active_model="account.move.line", active_ids=move_id.line_ids.ids
            )
            .create(
                {
                    "journal_id": self.company_data["default_journal_bank"].id,
                    "payment_date": fields.Date.today(),
                }
            )
        )
        return wizard

    def test_01_expense_wht_cert(self):
        """Test Expense Withholding Tax"""
        self.assertTrue(self.expense_sheet_wht_cert.expense_line_ids.wht_tax_id)
        self.expense_sheet_wht_cert.action_submit_sheet()
        self.expense_sheet_wht_cert.action_approve_expense_sheets()
        self.expense_sheet_wht_cert.action_sheet_move_post()
        self.assertEqual(self.expense_sheet_wht_cert.state, "post")

        move = self.expense_sheet_wht_cert.account_move_ids
        self.assertTrue(move.invoice_line_ids.wht_tax_id)

        payment_wizard = self._register_payment(move)
        self.assertEqual(
            payment_wizard.amount, 1000.0 - (1000.0 * (self.wht_1.amount / 100))
        )
        payment_wizard.action_create_payments()
        self.assertEqual(self.expense_sheet_wht_cert.state, "done")

    def test_02_expense_no_wht_cert(self):
        """Test Expense not Withholding Tax"""
        self.assertFalse(self.expense_sheet.expense_line_ids.wht_tax_id)
        self.expense_sheet.action_submit_sheet()
        self.expense_sheet.action_approve_expense_sheets()
        self.expense_sheet.action_sheet_move_post()
        self.assertEqual(self.expense_sheet.state, "post")
        payment_wizard = self._register_payment(self.expense_sheet.account_move_ids)
        self.assertEqual(payment_wizard.amount, 1000.0)
        payment_wizard.action_create_payments()
        self.assertEqual(self.expense_sheet.state, "done")

    def test_03_advance_clearing_more_wht_cert(self):
        """Test Clearing with Witholding Tax > Advance"""
        # ------------------ Advance --------------------------
        self.advance.action_submit_sheet()
        self.advance.action_approve_expense_sheets()
        self.advance.action_sheet_move_post()
        self.assertEqual(self.advance.clearing_residual, 1000.0)
        payment_wizard = self._register_payment(self.advance.account_move_ids)
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
        self.clearing_more.action_approve_expense_sheets()
        self.assertEqual(self.clearing_more.state, "approve")
        self.clearing_more.action_sheet_move_post()
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
            self.clearing_more.account_move_ids.button_cancel()
        # cancel withholding tax first
        self.clearing_more.wht_move_id.button_draft()
        self.assertEqual(self.clearing_more.wht_move_id.state, "draft")
        self.clearing_more.wht_move_id.button_cancel()
        self.assertEqual(self.clearing_more.wht_move_id.state, "cancel")
        # cancel clearing move
        move = self.clearing_more.account_move_ids
        move.button_cancel()
        self.assertEqual(move.state, "cancel")

    def test_04_advance_clearing_less_wht_cert(self):
        """Test Clearing with Witholding Tax < Advance"""
        # ------------------ Advance --------------------------
        self.advance.action_submit_sheet()
        self.advance.action_approve_expense_sheets()
        self.advance.action_sheet_move_post()
        self.assertEqual(self.advance.clearing_residual, 1000.0)
        payment_wizard = self._register_payment(self.advance.account_move_ids)
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
        self.clearing_less.action_approve_expense_sheets()
        self.clearing_less.action_sheet_move_post()
        # clearing < advance, it will change state to done
        self.assertEqual(self.clearing_less.state, "done")

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
        self.assertEqual(self.clearing_less.advance_sheet_residual, 200.0)
        self.assertEqual(self.clearing_less.wht_move_id.state, "draft")
        self.clearing_less.wht_move_id.action_post()
        self.assertEqual(self.clearing_less.wht_move_id.state, "posted")
        self.assertTrue(self.clearing_less.wht_move_id.has_wht)

        # Get sum amount residual from wht_line and ml reconcile
        wht_line = self.clearing_less.wht_move_id.line_ids.filtered(
            lambda line: line.account_id == self.advance_account
        )
        advance_ml = self.advance.account_move_ids.line_ids.filtered(
            lambda line: line.account_id == self.advance_account
        )
        ml_reconcile = advance_ml._all_reconciled_lines() + wht_line
        self.assertEqual(sum(ml_reconcile.mapped("amount_residual")), 208.0)
        # it should not cancel clearing, if there are withholding tax
        with self.assertRaises(UserError):
            self.clearing_less.account_move_ids.button_cancel()
        # cancel withholding tax first
        self.clearing_less.wht_move_id.button_draft()
        self.assertEqual(self.clearing_less.wht_move_id.state, "draft")
        self.clearing_less.wht_move_id.button_cancel()
        self.assertEqual(self.clearing_less.wht_move_id.state, "cancel")
        # cancel clearing move
        move = self.clearing_less.account_move_ids
        move.button_cancel()
        self.assertEqual(move.state, "cancel")
