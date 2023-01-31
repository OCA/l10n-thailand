# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestGovHrExpense(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sheet_model = cls.env["hr.expense.sheet"]
        cls.hr_model = cls.env["hr.expense"]
        cls.pr_model = cls.env["purchase.request"]
        cls.reminder_model = cls.env["reminder.definition"]
        cls.payment_register_model = cls.env["account.payment.register"]
        cls.product = cls.env.ref("l10n_th_gov_purchase_request.product_type_001")
        cls.procurement_type1 = cls.env.ref(
            "l10n_th_gov_purchase_request.procurement_type_001"
        )
        cls.procurement_method1 = cls.env.ref(
            "l10n_th_gov_purchase_request.procurement_specific"
        )
        cls.purchase_type3 = cls.env.ref(
            "l10n_th_gov_purchase_request.purchase_type_003"
        )
        cls.expense_product = cls.env.ref("hr_expense.product_product_zero_cost")
        cls.partner1 = cls.env.ref("base.res_partner_12")
        cls.employee1 = cls.env.ref("hr.employee_hne")
        cls.employee1.address_home_id = cls.partner1.id
        cls.journal_bank = cls.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )

        # Config advance
        cls.advance_account = cls.env["account.account"].create(
            {
                "code": "154000",
                "name": "Employee Advance",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_current_assets"
                ).id,
                "reconcile": True,
            }
        )
        cls.emp_advance = cls.env.ref("hr_expense_advance_clearing.product_emp_advance")
        cls.emp_advance.property_account_expense_id = cls.advance_account

        # Config Reminder
        cls.reminder = cls.reminder_model.create({"name": "Overdue Reminder"})

        # Create purchase request
        cls.purchase_request = cls.pr_model.create(
            {
                "procurement_type_id": cls.procurement_type1.id,
                "procurement_method_id": cls.procurement_method1.id,
                "purchase_type_id": cls.purchase_type3.id,
                "state": "approved",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "name": cls.product.name,
                            "product_uom_id": cls.product.uom_id.id,
                            "estimated_cost": 100.0,
                            "product_qty": 1,
                        },
                    )
                ],
            }
        )

    def test_01_create_expense_ref_pr(self):
        # Create expense sheet
        with Form(self.sheet_model) as s:
            s.name = "Expense test"
            s.employee_id = self.employee1
            s.purchase_request_id = self.purchase_request
        sheet = s.save()

        self.assertEqual(len(sheet.expense_line_ids), 1)
        self.assertTrue(self.purchase_request.expense_sheet_ids)
        for expense in sheet.expense_line_ids:
            self.assertEqual(
                expense.purchase_type_id, self.purchase_request.purchase_type_id
            )
        pr_view_ex = self.purchase_request.action_view_expense_sheet()
        self.assertEqual(pr_view_ex["res_id"], sheet.id)
        # Not allow reset to draft PR when related EX
        with self.assertRaises(UserError):
            self.purchase_request.button_draft()
        # Not allow rejected PR when related EX
        with self.assertRaises(UserError):
            self.purchase_request.button_rejected()

        # Test change unit amount more than PR
        with self.assertRaises(UserError):
            sheet.expense_line_ids.unit_amount = 150.0
            sheet.action_submit_sheet()
        sheet.action_submit_sheet()
        self.assertEqual(sheet.state, "submit")
        # Test change state PR is not approved. it shouldn't approve EX
        with self.assertRaises(UserError):
            self.purchase_request.state = "draft"
            sheet.approve_expense_sheets()
        sheet.approve_expense_sheets()
        self.assertEqual(sheet.state, "approve")
        sheet.action_sheet_move_create()
        self.assertEqual(sheet.state, "post")
        self.assertEqual(sheet.account_move_id.expense_sheet_count, 1)
        move_view_ex = sheet.account_move_id.action_view_expense_sheet()
        self.assertEqual(move_view_ex["res_id"], sheet.id)

    def test_02_create_av_ref_pr(self):
        today = fields.Date.today()
        # Create advance sheet
        with Form(self.sheet_model.with_context(default_advance=True)) as s:
            s.name = "Expense test"
            s.employee_id = self.employee1
            s.clearing_term = "thirty_days_after_return"
            s.date_return = today
            s.purchase_request_id = self.purchase_request
        advance = s.save()
        self.assertEqual(len(advance.expense_line_ids), 1)
        self.assertEqual(advance.clearing_date_due, today + relativedelta(days=29))

        # Test clearing term after receive, it will not compute clearing due date
        advance.clearing_term = "thirty_days_after_receive"
        self.assertFalse(advance.clearing_date_due)
        advance.action_submit_sheet()
        advance.approve_expense_sheets()
        advance.action_sheet_move_create()

        ctx = {
            "active_ids": [advance.account_move_id.id],
            "active_id": advance.account_move_id.id,
            "active_model": "account.move",
        }
        payment_date = today + relativedelta(days=10)
        with Form(self.payment_register_model.with_context(**ctx)) as f:
            f.journal_id = self.journal_bank
            f.payment_date = payment_date
        payment_wizard = f.save()
        payment_wizard.action_create_payments()
        self.assertEqual(advance.state, "done")
        self.assertEqual(
            advance.clearing_date_due, payment_date + relativedelta(days=29)
        )

        # Create Expense with related PR
        with Form(self.sheet_model) as s:
            s.name = "Clearing test"
            s.employee_id = self.employee1
            s.purchase_request_id = self.purchase_request
        sheet = s.save()
        self.assertEqual(len(sheet.expense_line_ids), 1)

        # Check related PR and multi EX
        pr_view_ex = self.purchase_request.action_view_expense_sheet()
        self.assertEqual(pr_view_ex["domain"][0][2], [sheet.id, advance.id])

        # Change document to Clearing, PR will not related clearing
        self.assertTrue(sheet.purchase_request_id)
        sheet.advance_sheet_id = advance.id
        sheet._onchange_advance_sheet_id()
        self.assertFalse(sheet.purchase_request_id)
