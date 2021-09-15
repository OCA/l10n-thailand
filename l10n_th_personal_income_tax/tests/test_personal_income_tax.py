# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, SavepointCase


class TestPersonalIncomeTax(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Account = cls.env["account.account"]
        cls.AccountJournal = cls.env["account.journal"]
        cls.AccountMove = cls.env["account.move"]
        cls.AccountPayment = cls.env["account.payment"]
        cls.PaymentRegister = cls.env["account.payment.register"]
        cls.PersonalIncomeTax = cls.env["personal.income.tax"]
        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.partner2 = cls.env.ref("base.res_partner_2")
        cls.current_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.user_type_expense = cls.env.ref("account.data_account_type_expenses")
        cls.journal_purchase = cls.AccountJournal.create(
            {"name": "purchase_0", "code": "PRCHASE0", "type": "purchase"}
        )
        cls.account_expense = cls.Account.search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_expenses").id,
                ),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )
        cls.wt_account = cls.Account.create(
            {
                "code": "XX152000",
                "name": "Withholding Tax Account Test",
                "user_type_id": cls.current_asset.id,
            }
        )
        cls.account_expense_product = cls.env["account.account"].create(
            {
                "code": "EXPENSE_PROD111",
                "name": "Expense - Test Account",
                "user_type_id": cls.user_type_expense.id,
            }
        )
        cls.pit_table = cls.PersonalIncomeTax.search([], limit=1)

    def _create_bill(self, partner, amount, pit=False, income_type=False):
        return self.AccountMove.create(
            {
                "move_type": "in_invoice",
                "partner_id": partner.id,
                "invoice_date": fields.Date.today(),
                "journal_id": self.journal_purchase.id,
                "account_pit": pit,
                "pit_wt_cert_income_type": income_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line1",
                            "account_id": self.account_expense_product.id,
                            "quantity": 1.0,
                            "price_unit": amount,
                        },
                    )
                ],
            }
        )

    def _get_payment_wizard(self, move):
        action = move.action_register_payment()
        ctx = action.get("context")
        if move._context.get("pit_date", False):
            ctx["pit_date"] = move._context.get("pit_date")
        with Form(self.PaymentRegister.with_context(ctx)) as f:
            if f.payment_difference:
                f.writeoff_account_id = self.wt_account
            register_payment = f.save()
        return register_payment

    def _auto_create_bill_to_payment(self, partner, amount, amount_diff=0.0):
        bill = self._create_bill(partner, amount, pit=True, income_type=str(1))
        bill.action_post()
        register_payment = self._get_payment_wizard(bill)
        self.assertEqual(register_payment.amount, amount - amount_diff)
        payment = register_payment.action_create_payments()
        payment_id = self.AccountPayment.browse(payment.get("res_id"))
        return payment_id

    def test_01_pit_rate_table(self):
        # Rate range must start 0.0
        with self.assertRaises(UserError):
            self.pit_table.rate_ids[0].income_from = 1
            self.pit_table._check_rate_ids()
        self.assertEqual(
            self.pit_table.rate_ids[1].income_from, self.pit_table.rate_ids[0].income_to
        )
        # Income From must equal Previous Income To
        with self.assertRaises(UserError):
            self.pit_table.rate_ids[1].income_from = (
                self.pit_table.rate_ids[0].income_to + 1
            )
            self.pit_table._check_rate_ids()

    def test_02_pit_validation(self):
        bill_test_1 = self._create_bill(
            self.partner1, 10000, pit=True, income_type=str(1)
        )
        bill_test_2 = self._create_bill(
            self.partner2, 10000, pit=True, income_type=str(1)
        )
        # PIT can not register multi move
        with self.assertRaises(UserError):
            self._get_payment_wizard(bill_test_1 + bill_test_2)

        # No PIT Rate Table on calendat 2001
        bill_test_1.action_post()
        with self.assertRaises(ValidationError):
            self._get_payment_wizard(
                bill_test_1.with_context(pit_date=fields.Date.from_string("2001-01-01"))
            )

    def test_03_pit_from_bills(self):
        """
        PIT Table Rate Thailand 2021:
        ===============================================
        Income From (>)| Income To (<=)| Tax Rate (%) |
        ===============================================
        0.0            |    150,000    |            0 |
        150,000        |    300,000    |            5 |
        300,000        |    500,000    |           10 |
        500,000        |    750,000    |           15 |
        750,000        |  1,000,000    |           20 |
        1,000,000      |  2,000,000    |           25 |
        2,000,000      |  4,000,000    |           30 |
        4,000,000      |        MAX    |           35 |
        -----------------------------------------------
        """
        self.assertFalse(self.partner1.pit_line)

        # PIT 0 -> 70,000 (Tax: 0%)
        bill1 = self._create_bill(self.partner1, 70000, pit=True, income_type=str(1))
        self.assertEqual(bill1.state, "draft")
        self.assertTrue(bill1.account_pit)
        bill1.action_post()
        self.assertEqual(bill1.state, "posted")
        register_payment = self._get_payment_wizard(bill1)
        self.assertEqual(register_payment.amount, 70000)
        payment = register_payment.action_create_payments()
        payment_id = self.AccountPayment.browse(payment.get("res_id"))
        self.assertTrue(payment_id.pit_line)
        self.assertTrue(self.partner1.pit_line)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_income")), 70000.0)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_wt")), 0.0)

        # Case increase amount:  70,000 -> 210,000 (Tax: 5%)
        amount_wt = 3000.0  # calculated from steps WHT Thailand
        self._auto_create_bill_to_payment(self.partner1, 140000.0, 3000)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_income")), 210000.0)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_wt")), amount_wt)

        # Case reduct amount: PIT 210,000 -> 250,000 (Tax: 10%)
        amount_wt += 2000
        payment_id = self._auto_create_bill_to_payment(self.partner1, 40000.0, 2000)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_income")), 250000.0)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_wt")), amount_wt)

        # Case cancel payment with PIT
        self.assertEqual(len(self.partner1.pit_line.filtered("cancelled")), 0)
        self.assertEqual(payment_id.state, "posted")
        payment_id.action_cancel()
        self.assertEqual(payment_id.state, "cancel")
        self.assertEqual(len(self.partner1.pit_line.filtered("cancelled")), 1)
        self.assertEqual(sum(self.partner1.pit_line.mapped("amount_income")), 210000.0)
        self.assertEqual(
            sum(self.partner1.pit_line.mapped("amount_wt")), amount_wt - 2000
        )

        # Action view summary PIT yearly
        report_yearly = self.partner1.action_view_pit_yearly_summary()
        self.assertEqual(report_yearly.get("res_model"), "pit.move.yearly")
