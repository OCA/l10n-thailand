# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.l10n_th_account_tax.tests.test_withholding_tax import (
    TestWithholdingTax,
)


@tagged("post_install", "-at_install")
class TestAccountTaxMulti(TestWithholdingTax):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_model = cls.env["account.payment"]
        cls.register_view_id = "account.view_account_payment_register_form"

    def _create_invoice(
        self,
        partner_id,
        journal_id,
        invoice_type,
        line_account_id,
        price_unit,
        product_id=False,
        no_tax=True,
        multi=False,
    ):
        invoice_dict = {
            "name": "/",
            "partner_id": partner_id,
            "journal_id": journal_id,
            "move_type": invoice_type,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": product_id,
                        "quantity": 1.0,
                        "account_id": line_account_id,
                        "name": "Advice1",
                        "price_unit": price_unit or 0.0,
                    }
                )
            ],
        }
        if multi:
            invoice_dict["invoice_line_ids"].append(
                Command.create(
                    {
                        "product_id": product_id,
                        "quantity": 1.0,
                        "account_id": line_account_id,
                        "name": "Advice2",
                        "price_unit": price_unit or 0.0,
                    }
                )
            )
        invoice = self.move_obj.create(invoice_dict)
        if no_tax:
            invoice.invoice_line_ids.write({"tax_ids": False})
        return invoice

    def test_01_create_payment_withholding_tax(self):
        price_unit = 100.0
        # Don't allow to change account_id
        with self.assertRaises(ValidationError):
            self.wht_3.write({"account_id": self.expense_account.id})

        # Create invoices without withholding tax
        invoice = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        invoice2 = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
        )
        # Add withholding tax 3% to invoice
        self.assertFalse(invoice.invoice_line_ids.wht_tax_id)
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        self.assertTrue(invoice.invoice_line_ids.wht_tax_id)
        invoice.action_post()

        # Test register payment with multi invoice,
        # but invoice2 is still open, it should error
        invoices = invoice | invoice2
        with self.assertRaisesRegex(
            UserError, r"You can only register payment for posted journal entries."
        ):
            Form.from_action(self.env, invoices.action_register_payment())

        # Test register payment with single invoice
        with Form.from_action(self.env, invoice.action_register_payment()) as wiz_form:
            self.assertEqual(wiz_form.payment_difference_handling, "reconcile")
            self.assertEqual(wiz_form.amount, price_unit * 0.97)
            self.assertEqual(wiz_form.payment_difference, price_unit * 0.03)
            self.assertEqual(wiz_form.writeoff_label, "Withholding Tax 3%")
            self.assertEqual(wiz_form.writeoff_account_id, self.wht_3.account_id)

    def test_02_create_payment_multi_withholding_tax_multi_line(self):
        """Create payment with 2 withholding tax on 2 line"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            multi=True,
        )
        # Add multi withholding tax
        self.assertFalse(invoice.invoice_line_ids.wht_tax_id)
        invoice.invoice_line_ids[0].wht_tax_id = self.wht_3
        invoice.invoice_line_ids[1].wht_tax_id = self.wht_1
        self.assertTrue(invoice.invoice_line_ids.wht_tax_id)
        invoice.action_post()

        # Test register payment with single invoice multi withholding tax
        with Form.from_action(self.env, invoice.action_register_payment()) as wiz_form:
            self.assertEqual(
                wiz_form.payment_difference_handling, "reconcile_multi_deduct"
            )
            self.assertTrue(wiz_form.deduction_ids)
            register_payment = wiz_form.save()

        # Test change withholding tax from 3% to 1%, it should error
        # because total amount deduction is not equal to payment difference
        with self.assertRaisesRegex(UserError, r"The total deduction should be"):
            with Form(register_payment) as f:
                with f.deduction_ids.edit(0) as line:
                    line.wht_tax_id = self.wht_1

        # But if we change the amount to 198, it should be OK
        with Form(register_payment) as f:
            with f.deduction_ids.edit(0) as line:
                line.wht_tax_id = self.wht_1
            f.amount = 198
        payment = register_payment._create_payments()
        self.assertEqual(payment.state, "paid")
        self.assertEqual(
            payment.amount,
            (price_unit * 2) - sum(register_payment.deduction_ids.mapped("amount")),
        )

    def test_03_create_payment_one_withholding_tax_multi_line(self):
        """Create payment with 1 withholding tax on 2 line"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            multi=True,
        )
        self.assertFalse(invoice.invoice_line_ids.wht_tax_id)
        invoice.invoice_line_ids[0].wht_tax_id = self.wht_3
        invoice.invoice_line_ids[1].wht_tax_id = self.wht_3
        self.assertTrue(invoice.invoice_line_ids.mapped("wht_tax_id"))
        invoice.action_post()

        # Test register payment with single invoice multi withholding tax (same value)
        with Form.from_action(self.env, invoice.action_register_payment()) as wiz_form:
            self.assertEqual(wiz_form.payment_difference_handling, "reconcile")
            payment_id = wiz_form.save()._create_payments()

        payment = self.payment_model.browse(payment_id.id)
        self.assertEqual(payment.state, "paid")
        self.assertEqual(
            payment.amount,
            invoice.amount_total - invoice.amount_untaxed * (self.wht_3.amount / 100),
        )

    def test_04_create_payment_multi_withholding_keep_open(self):
        """Create payment with 2 withholding tax on 2 line and keep open 1"""
        price_unit = 100.0
        invoice = self._create_invoice(
            self.partner_1.id,
            self.purchase_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit,
            multi=True,
        )
        self.assertFalse(invoice.invoice_line_ids.wht_tax_id)
        invoice.invoice_line_ids[0].wht_tax_id = self.wht_3
        invoice.invoice_line_ids[1].wht_tax_id = self.wht_1
        self.assertTrue(invoice.invoice_line_ids.mapped("wht_tax_id"))
        invoice.action_post()

        # Test register payment with single invoice multi withholding tax (same value)
        with Form.from_action(self.env, invoice.action_register_payment()) as wiz_form:
            self.assertEqual(
                wiz_form.payment_difference_handling, "reconcile_multi_deduct"
            )
            self.assertTrue(wiz_form.deduction_ids)
            register_payment = wiz_form.save()

        # Keep 3% and deduct 5%
        deduct_3 = register_payment.deduction_ids.filtered(
            lambda deduct: deduct.wht_tax_id == self.wht_3
        )
        with Form(deduct_3) as deduct:
            deduct.is_open = True
        self.assertFalse(deduct.wht_tax_id)

        payment_id = register_payment._create_payments()
        payment = self.payment_model.browse(payment_id.id)
        self.assertEqual(len(payment.move_id), 1)
        # check reconcile
        self.assertEqual(invoice.payment_state, "partial")
        self.assertFalse(payment.move_id.mapped("line_ids").mapped("full_reconcile_id"))

        # paid residual, it should be reconcile
        with Form.from_action(self.env, invoice.action_register_payment()) as wiz_form:
            wiz_form.amount = 0
            wiz_form.deduction_ids.remove(index=1)
            register_payment = wiz_form.save()

        register_payment.action_create_payments()
        self.assertEqual(invoice.payment_state, "paid")
        self.assertTrue(payment.move_id.mapped("line_ids").mapped("full_reconcile_id"))

    # TODO: test for PIT cases
