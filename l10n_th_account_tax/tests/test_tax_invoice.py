# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import new_test_user

from .common import ThAccountTaxCommon


@tagged("post_install", "-at_install")
@freeze_time("2026-06-15")
class TestTaxInvoice(ThAccountTaxCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.purchase_wht = cls._create_wht_tax("Purchase WHT -3%")

        # ==== Cash Basis Taxes setup ====
        cls.journal_undue = cls.env["account.journal"].create(
            {"name": "UndueVAT", "type": "general", "code": "UNDUE"}
        )
        cls.env.company.tax_cash_basis_journal_id = cls.journal_undue.id
        cls.env.company.tax_exigibility = True
        cls.tax_group_undue_vat = cls.env["account.tax.group"].create(
            {"name": "UndueVAT"}
        )

        # ==== Chart of Account setup ====
        cls.undue_output_vat_acct = cls._create_account(
            "DO7", "DO7", "asset_current", reconcile=True
        )
        cls.input_zero_vat_acct = cls._create_account("V0", "V0", "liability_current")
        cls.undue_input_vat_acct = cls._create_account(
            "DV7", "DV7", "asset_current", reconcile=True
        )
        cls.undue_recon_input_vat_acct = cls._create_account(
            "DV7 (Reconcile)", "DV7rec", "asset_current", reconcile=True
        )

        # ==== Taxes setup ====
        cls.undue_output_vat = cls._create_vat_tax(
            "DO7",
            "sale",
            7.0,
            cls.output_vat_acct,
            tax_group=cls.tax_group_undue_vat,
            exigibility="on_payment",
            transition_account=cls.undue_output_vat_acct,
        )
        cls.input_zero_vat = cls._create_vat_tax(
            "V0",
            "purchase",
            0.0,
            cls.input_zero_vat_acct,
            tax_group=cls.tax_group_vat,
        )
        cls.undue_input_vat = cls._create_vat_tax(
            "DV7",
            "purchase",
            7.0,
            cls.input_vat_acct,
            tax_group=cls.tax_group_undue_vat,
            exigibility="on_payment",
            transition_account=cls.undue_input_vat_acct,
        )
        cls.undue_input_reconcile_vat = cls._create_vat_tax(
            "DV7 (reconcile)",
            "purchase",
            7.0,
            cls.input_vat_acct,
            tax_group=cls.tax_group_undue_vat,
            exigibility="on_payment",
            transition_account=cls.undue_recon_input_vat_acct,
        )

        # Optiona tax sequence
        cls.cust_vat_sequence = cls.env["ir.sequence"].create(
            {"name": "Cust VAT Sequence", "padding": 4}
        )

        # Prepare Supplier Invoices
        cls.supplier_invoice_vat = cls._create_th_invoice(
            "in_invoice", [(100, cls.input_vat)], partner=cls.partner
        )
        cls.supplier_invoice_undue_vat = cls._create_th_invoice(
            "in_invoice", [(100, cls.undue_input_vat)], partner=cls.partner
        )
        cls.supplier_invoice_undue_vat_partial = cls.supplier_invoice_undue_vat.copy(
            {"invoice_date": fields.Date.today()}
        )
        cls.supplier_invoice_undue_vat_reconcile = cls._create_th_invoice(
            "in_invoice", [(100, cls.undue_input_reconcile_vat)], partner=cls.partner
        )
        cls.supplier_invoice_zero_vat = cls._create_th_invoice(
            "in_invoice", [(100, cls.input_zero_vat)], partner=cls.partner
        )
        cls.supplier_refund_undue_vat = cls._create_th_invoice(
            "in_refund", [(100, cls.undue_input_vat)], partner=cls.partner
        )

        # Prepare Customer Invoices
        cls.customer_invoice_vat = cls._create_th_invoice(
            "out_invoice", [(100, cls.output_vat)], partner=cls.partner
        )
        cls.customer_invoice_vat_seq = cls.customer_invoice_vat.copy()
        cls.customer_invoice_undue_vat = cls._create_th_invoice(
            "out_invoice", [(100, cls.undue_output_vat)], partner=cls.partner
        )
        cls.customer_invoice_undue_vat_seq = cls.customer_invoice_undue_vat.copy()

    def _create_manual_vat_entry(self, manual_tax_invoice=True, journal=None):
        return self._create_entry(
            [
                {
                    "name": "Expense",
                    "account_id": self.expense_account.id,
                    "debit": 1000.0,
                },
                {
                    "name": "Manual input VAT",
                    "partner_id": self.partner.id,
                    "account_id": self.input_vat_acct.id,
                    "debit": 70.0,
                    "manual_tax_invoice": manual_tax_invoice,
                },
                {
                    "name": "Payable",
                    "account_id": self.payable_account.id,
                    "credit": 1070.0,
                },
            ],
            journal=journal,
            partner_id=self.partner.id,
        )

    def test_01_supplier_invoice_vat(self):
        """Supplier Invoice with VAT,
        user must fill in Tax Invoice/Date on Invoice"""
        bill = self.supplier_invoice_vat
        # Draft tax invoice amounts follow the changes of the bill
        self.assertEqual(bill.tax_invoice_ids.tax_base_amount, 100)
        self.assertEqual(bill.tax_invoice_ids.balance, 7)
        bill.invoice_line_ids.price_unit = 200
        self.assertEqual(len(bill.tax_invoice_ids), 1)
        self.assertEqual(bill.tax_invoice_ids.tax_base_amount, 200)
        self.assertEqual(bill.tax_invoice_ids.balance, 14)
        bill.invoice_line_ids.price_unit = 100
        # A tax invoice can be duplicated, not the last one deleted
        original = bill.tax_invoice_ids
        duplicate = original.copy()
        self.assertEqual(len(bill.tax_invoice_ids), 2)
        self.assertEqual(duplicate.move_id, bill)
        self.assertEqual(duplicate.move_line_id, original.move_line_id)
        duplicate.unlink()
        self.assertEqual(len(bill.tax_invoice_ids), 1)
        with self.assertRaisesRegex(
            UserError, "Cannot delete this last tax invoice line"
        ):
            original.unlink()
        # Nor point at a journal item of another entry
        other_line = self.customer_invoice_vat.tax_invoice_ids.move_line_id
        self.assertTrue(other_line)
        message = "The journal item of a tax invoice must belong to its journal entry."
        with self.assertRaisesRegex(ValidationError, message):
            original.write({"move_line_id": other_line.id})
        with self.assertRaisesRegex(ValidationError, message):
            self.env["account.move.tax.invoice"].create(
                {"move_id": bill.id, "move_line_id": other_line.id}
            )
        # Internal users only read tax invoices, portal users have no access
        internal = new_test_user(
            self.env, login="th_tinv_internal", groups="base.group_user"
        )
        tax_invoice_as_internal = original.with_user(internal)
        self.assertEqual(tax_invoice_as_internal.balance, 7.0)
        with self.assertRaises(AccessError):
            tax_invoice_as_internal.write({"tax_invoice_number": "INTERNAL"})
        portal = new_test_user(
            self.env, login="th_tinv_portal", groups="base.group_portal"
        )
        with self.assertRaises(AccessError):
            original.with_user(portal).read(["tax_invoice_number"])
        action = self.env.ref("l10n_th_account_tax.action_tax_invoice")
        self.assertEqual(action.res_model, "account.move.tax.invoice")

        # User have not filled in Tax Invoice / Date in account_invoice_tax
        with self.assertRaises(UserError) as e:
            self.supplier_invoice_vat.action_post()
        self.assertEqual(e.exception.args[0], "Please fill in tax invoice and tax date")
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today()
        self.supplier_invoice_vat.tax_invoice_ids.tax_invoice_number = tax_invoice
        with self.assertRaises(UserError):
            self.supplier_invoice_vat.action_post()
        self.assertEqual(self.supplier_invoice_vat.state, "draft")
        self.supplier_invoice_vat.tax_invoice_ids.tax_invoice_date = tax_date
        self.supplier_invoice_vat.action_post()
        # Check report late 2 month, report date is not equal tax invoice date
        self.assertEqual(
            self.supplier_invoice_vat.tax_invoice_ids.report_date,
            self.supplier_invoice_vat.tax_invoice_ids.tax_invoice_date,
        )
        with Form(self.supplier_invoice_vat.tax_invoice_ids) as tax:
            tax.report_late_mo = "2"
        move_tax = tax.save()
        self.assertNotEqual(move_tax.report_date, move_tax.tax_invoice_date)

        # A VAT not restricted to purchases is a purchase tax invoice on a bill,
        # the vendor's number is kept when posting
        vat_none = self._create_vat_tax(
            "V7 (no scope)", "none", 7.0, self.input_vat_acct, self.tax_group_vat
        )
        bill = self._create_th_invoice(
            "in_invoice", [(1000, vat_none)], partner=self.partner
        )
        tax_invoice = bill.tax_invoice_ids
        self.assertEqual(len(tax_invoice), 1)
        self.assertTrue(tax_invoice._is_purchase_tax_invoice())
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            bill.action_post()
        self._fill_tax_invoice(bill, number="VENDOR-NONE-001")
        bill.action_post()
        self.assertEqual(tax_invoice.tax_invoice_number, "VENDOR-NONE-001")
        self.assertEqual(tax_invoice.tax_invoice_date, bill.date)
        self.assertEqual(tax_invoice.tax_base_amount, 1000)
        self.assertEqual(tax_invoice.balance, 70)

        # Withholding tax is computed on payment, without tax invoice
        bill = self._create_th_invoice(
            "in_invoice",
            [(1000, self.input_vat | self.purchase_wht)],
            partner=self.partner,
        )
        self.assertEqual(len(bill.tax_invoice_ids), 1)
        self.assertEqual(bill.tax_invoice_ids.tax_line_id, self.input_vat)
        self.assertFalse(
            bill.line_ids.filtered(lambda line: line.tax_line_id == self.purchase_wht)
        )
        self._fill_tax_invoice(bill, number="BILL-VAT-001")
        bill.action_post()
        payment = self._pay(bill, withhold="withhold_pay")
        self.assertFalse(payment.move_id.tax_invoice_ids)

    def test_02_supplier_invoice_undue_vat(self):
        """
        Vendor Undue VAT Process:
        1) Create a vendor bill with undue VAT and register the payment.
        2) A Cash Basis entry will be created in draft until the vendor's tax
            invoice number and date are entered.
        3) When `Clear Tax` on the payment document,
            a new wizard should open with the default accounting date set to today.
        4) After clearing the tax, the accounting date on the Cash Basis entry
            will update according to the wizard, and its state will change to "Posted"
        """
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today()
        self.supplier_invoice_undue_vat.action_post()
        # Undue VAT has no tax invoice on the bill, only on payments
        self.assertFalse(self.supplier_invoice_undue_vat.tax_invoice_ids)
        action = self.supplier_invoice_undue_vat.action_register_payment()
        ctx = action.get("context")
        self.assertFalse(
            self.supplier_invoice_undue_vat.tax_cash_basis_created_move_ids
        )
        # Make full payment from invoice
        with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
        payment_wiz = f.save()
        res = payment_wiz.action_create_payments()
        payment = self.env["account.payment"].browse(res.get("res_id"))
        self.assertTrue(payment.tax_invoice_ids)
        self.assertIn(payment.state, ("paid", "reconciled"))
        self.assertEqual(payment.tax_invoice_ids.payment_id, payment)
        self.assertFalse(payment.tax_invoice_ids.tax_invoice_number)
        self.assertFalse(payment.tax_invoice_ids.tax_invoice_date)
        self.assertTrue(payment.to_clear_tax)

        # Check button Journal Entry must have move_id and cash basis
        act_journal_entry = payment.button_open_journal_entry()
        payment_moves = payment.tax_invoice_move_ids + payment.move_id
        self.assertEqual(act_journal_entry["domain"][0][2], payment_moves.ids)

        # Cash Basis created and state is draft and no accounting date
        bill_tax_cash_basis = (
            self.supplier_invoice_undue_vat.tax_cash_basis_created_move_ids
        )
        self.assertEqual(len(bill_tax_cash_basis), 1)
        self.assertIn(bill_tax_cash_basis.name, (False, "/"))
        self.assertEqual(bill_tax_cash_basis.state, "draft")
        self.assertEqual(bill_tax_cash_basis.date, tax_date)
        self.assertFalse(bill_tax_cash_basis.tax_invoice_ids.tax_invoice_number)
        self.assertFalse(bill_tax_cash_basis.tax_invoice_ids.tax_invoice_date)

        # Resetting and reposting the payment keeps the draft cash basis entry.
        payment.action_draft()
        self.assertEqual(payment.state, "draft")
        self.assertEqual(payment.tax_invoice_move_ids, bill_tax_cash_basis)
        self.assertTrue(payment.to_clear_tax)
        payment.action_post()
        self.assertIn(payment.state, ("paid", "reconciled"))
        bill_tax_cash_basis = (
            self.supplier_invoice_undue_vat.tax_cash_basis_created_move_ids
        )
        self.assertEqual(len(bill_tax_cash_basis), 1)
        self.assertEqual(bill_tax_cash_basis, payment.tax_invoice_move_ids)
        self.assertEqual(bill_tax_cash_basis.state, "draft")
        self.assertIn(bill_tax_cash_basis.name, (False, "/"))

        # Clear tax cash basis
        with self.assertRaises(UserError) as e:
            payment.open_clear_tax()
        self.assertEqual(e.exception.args[0], "Please fill in tax invoice and tax date")
        with self.assertRaises(UserError):
            payment.clear_tax_cash_basis()
        with self.assertRaises(UserError):
            bill_tax_cash_basis.action_post()
        self.assertEqual(bill_tax_cash_basis.state, "draft")

        # Fill in tax invoice and clear undue vat
        payment.tax_invoice_ids.write(
            {"tax_invoice_number": tax_invoice, "tax_invoice_date": tax_date}
        )
        # Create Wizard Clear Tax
        action_clear = payment.open_clear_tax()
        self.assertEqual(action_clear["res_model"], "clear.tax")
        self.assertEqual(action_clear["context"]["default_payment_id"], payment.id)
        clear_date = fields.Date.from_string("2025-01-01")
        clear_tax_wiz = self.env["clear.tax"].create(
            {"payment_id": payment.id, "date": clear_date}
        )
        clear_tax_wiz.action_clear_tax()
        # Cash basis journal is now posted
        bill_tax_cash_basis = (
            self.supplier_invoice_undue_vat.tax_cash_basis_created_move_ids
        )
        self.assertEqual(len(bill_tax_cash_basis), 1)
        self.assertNotIn(False, bill_tax_cash_basis.mapped("name"))
        self.assertNotIn("/", bill_tax_cash_basis.mapped("name"))
        self.assertEqual(bill_tax_cash_basis.state, "posted")
        # Tax cash basis will change accounting date from clear tax
        self.assertEqual(bill_tax_cash_basis.date, clear_date)
        self.assertEqual(payment.tax_invoice_ids.tax_invoice_date, tax_date)
        self.assertEqual(payment.tax_invoice_ids.tax_invoice_number, tax_invoice)
        self.assertFalse(payment.to_clear_tax)
        # Check the move_line_ids, from both Bank and Cash Basis journal
        self.assertTrue(payment.move_id)
        self.assertTrue(payment.tax_invoice_move_ids)

    def test_03_supplier_invoice_undue_vat_reconcile(self):
        """Register Payment from Vendor Invoice"""
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today()
        self.supplier_invoice_undue_vat_reconcile.action_post()
        action = self.supplier_invoice_undue_vat_reconcile.action_register_payment()
        ctx = action.get("context")
        self.assertFalse(
            self.supplier_invoice_undue_vat_reconcile.tax_cash_basis_created_move_ids
        )
        # Make full payment from invoice
        with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
        payment_wiz = f.save()
        res = payment_wiz.action_create_payments()
        payment = self.env["account.payment"].browse(res.get("res_id"))
        self.assertTrue(payment.tax_invoice_ids)
        self.assertIn(payment.state, ("paid", "reconciled"))
        self.assertEqual(payment.tax_invoice_ids.payment_id, payment)
        self.assertFalse(payment.tax_invoice_ids.tax_invoice_number)
        self.assertFalse(payment.tax_invoice_ids.tax_invoice_date)
        self.assertTrue(payment.to_clear_tax)
        # Cash Basis created and state is draft
        bill_tax_cash_basis = (
            self.supplier_invoice_undue_vat_reconcile.tax_cash_basis_created_move_ids
        )
        self.assertEqual(len(bill_tax_cash_basis), 1)
        self.assertIn(bill_tax_cash_basis.name, (False, "/"))
        self.assertEqual(bill_tax_cash_basis.state, "draft")
        # Resetting and reposting the payment keeps the draft cash basis entry.
        payment.action_draft()
        self.assertEqual(payment.state, "draft")
        self.assertEqual(payment.tax_invoice_move_ids, bill_tax_cash_basis)
        self.assertTrue(payment.to_clear_tax)
        payment.action_post()
        self.assertIn(payment.state, ("paid", "reconciled"))
        bill_tax_cash_basis = (
            self.supplier_invoice_undue_vat_reconcile.tax_cash_basis_created_move_ids
        )
        self.assertEqual(len(bill_tax_cash_basis), 1)
        self.assertEqual(bill_tax_cash_basis, payment.tax_invoice_move_ids)
        self.assertEqual(bill_tax_cash_basis.state, "draft")
        self.assertIn(bill_tax_cash_basis.name, (False, "/"))

        # Clear tax cash basis
        with self.assertRaises(UserError) as e:
            payment.open_clear_tax()
        self.assertEqual(e.exception.args[0], "Please fill in tax invoice and tax date")
        with self.assertRaises(UserError):
            payment.clear_tax_cash_basis()
        with self.assertRaises(UserError):
            bill_tax_cash_basis.action_post()

        # Fill in tax invoice and clear undue vat
        payment.tax_invoice_ids.write(
            {"tax_invoice_number": tax_invoice, "tax_invoice_date": tax_date}
        )

        # Create Wizard Clear Tax
        action_clear = payment.open_clear_tax()
        self.assertEqual(action_clear["res_model"], "clear.tax")
        self.assertEqual(action_clear["context"]["default_payment_id"], payment.id)
        clear_date = fields.Date.from_string("2025-01-01")
        clear_tax_wiz = self.env["clear.tax"].create(
            {"payment_id": payment.id, "date": clear_date}
        )
        clear_tax_wiz.action_clear_tax()

        # Cash basis journal is now posted
        bill_tax_cash_basis = (
            self.supplier_invoice_undue_vat_reconcile.tax_cash_basis_created_move_ids
        )
        self.assertEqual(len(bill_tax_cash_basis), 1)
        self.assertNotIn(False, bill_tax_cash_basis.mapped("name"))
        self.assertNotIn("/", bill_tax_cash_basis.mapped("name"))
        self.assertEqual(bill_tax_cash_basis.state, "posted")
        self.assertEqual(bill_tax_cash_basis.date, clear_date)
        self.assertEqual(payment.tax_invoice_ids.tax_invoice_number, tax_invoice)
        self.assertEqual(payment.tax_invoice_ids.tax_invoice_date, tax_date)
        self.assertFalse(payment.to_clear_tax)
        # Check the move_line_ids, from both Bank and Cash Basis journal
        self.assertTrue(payment.move_id)
        self.assertTrue(payment.tax_invoice_move_ids)

    def test_04_supplier_invoice_undue_vat_partial_payment(self):
        """Register partial payments from vendor invoice, each payment has its own
        undue VAT entry and tax invoice, cleared separately"""
        # Pay half of a 1,070 bill, including half of the undue VAT.
        invoice = self.supplier_invoice_undue_vat_partial
        invoice.invoice_line_ids.price_unit = 1000
        invoice.action_post()
        payments = self.env["account.payment"]
        for installment, payment_date in enumerate(("2026-06-15", "2026-07-15")):
            ctx = invoice.action_register_payment().get("context")
            with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
                f.journal_id = self.bank_journal
                f.payment_date = fields.Date.to_date(payment_date)
                if not installment:
                    f.amount = 535
                    f.payment_difference_handling = "open"
            res = f.save().action_create_payments()
            payment = self.env["account.payment"].browse(res.get("res_id"))
            self.assertIn(payment.state, ("paid", "reconciled"))
            self.assertEqual(payment.amount, 535)
            self.assertNotIn(payment, payments)
            payments |= payment
            self.assertEqual(
                invoice.payment_state, "paid" if installment else "partial"
            )
            self.assertEqual(invoice.amount_residual, 535 * (1 - installment))
            tax_invoice = payment.tax_invoice_ids
            self.assertEqual(len(tax_invoice), 1)
            self.assertEqual(tax_invoice.payment_id, payment)
            self.assertEqual(tax_invoice.move_id, payment.tax_invoice_move_ids)
            self.assertEqual(tax_invoice.tax_base_amount, 500)
            self.assertEqual(tax_invoice.balance, 35)
            self.assertFalse(tax_invoice.tax_invoice_number)
            self.assertFalse(tax_invoice.tax_invoice_date)
            self.assertTrue(payment.to_clear_tax)
            self.assertEqual(payment.tax_invoice_move_ids.state, "draft")
        payment_1, payment_2 = payments

        # One undue VAT entry per payment, still waiting for the vendor's tax invoice
        cash_basis_moves = invoice.tax_cash_basis_created_move_ids
        self.assertEqual(len(cash_basis_moves), 2)
        self.assertEqual(
            payment_1.tax_invoice_move_ids | payment_2.tax_invoice_move_ids,
            cash_basis_moves,
        )
        self.assertFalse(
            payment_1.tax_invoice_move_ids & payment_2.tax_invoice_move_ids
        )
        all_tax_invoices = cash_basis_moves.tax_invoice_ids
        self.assertEqual(all_tax_invoices, payments.tax_invoice_ids)
        self.assertEqual(sum(all_tax_invoices.mapped("tax_base_amount")), 1000)
        self.assertEqual(sum(all_tax_invoices.mapped("balance")), 70)

        # Clearing the first payment leaves the second one waiting
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            payment_1.open_clear_tax()
        payment_1.tax_invoice_ids.write(
            {
                "tax_invoice_number": "SINV-INST-001",
                "tax_invoice_date": fields.Date.to_date("2026-06-12"),
            }
        )
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            payment_2.open_clear_tax()
        payment_1.clear_tax_cash_basis()
        self.assertEqual(payment_1.tax_invoice_move_ids.state, "posted")
        self.assertFalse(payment_1.to_clear_tax)
        self.assertEqual(payment_1.tax_invoice_ids.tax_invoice_number, "SINV-INST-001")
        self.assertEqual(payment_2.tax_invoice_move_ids.state, "draft")
        self.assertTrue(payment_2.to_clear_tax)

        # Not allow delete tax invoice if it has 1 line.
        with self.assertRaises(UserError):
            payment_2.tax_invoice_ids.unlink()
        self.assertEqual(len(payment_2.tax_invoice_ids), 1)
        payment_2.tax_invoice_ids.with_context(force_remove_tax_invoice=1).unlink()
        self.assertEqual(len(payment_2.tax_invoice_ids), 0)

    def test_05_supplier_invoice_undue_vat_je(self):
        """Case on undue vat, to net JE with vendor bill.
        No cash basis entry, as there is no payment."""
        # Post suupplier invoice
        invoice = self.supplier_invoice_undue_vat.copy()
        invoice.invoice_date = invoice.date
        invoice.action_post()

        payable_account = invoice.partner_id.property_account_payable_id

        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "line_ids": [
                    Command.create(
                        {
                            "name": "Payable",
                            "account_id": payable_account.id,
                            "partner_id": invoice.partner_id.id,
                            "balance": 107.0,  # debit
                        }
                    ),
                    Command.create(
                        {
                            "name": "undue_tax_line_1",
                            "account_id": self.undue_recon_input_vat_acct.id,
                            "balance": -7.0,  # Undue credit
                        },
                    ),
                    Command.create(
                        {
                            "name": "Expense",
                            "account_id": self.input_vat_acct.id,
                            "balance": -100.0,  # credit
                        },
                    ),
                ],
            }
        )
        move.action_post()

        self.assertEqual(move.state, invoice.state)

        # At invoice add journal entry to reconcile
        je_ml = move.line_ids.filtered(lambda line: line.account_id == payable_account)
        invoice.js_assign_outstanding_line(je_ml.id)

        # Standard creates undue VAT entries on payments only, not when
        # netting with a journal entry
        self.assertTrue(je_ml.reconciled)
        self.assertFalse(invoice.tax_cash_basis_created_move_ids)

        # Test unreconcile invoice and journal entry
        partial_reconcile = self.env["account.partial.reconcile"].search(
            [("debit_move_id", "=", je_ml.id)]
        )
        invoice.js_remove_outstanding_partial(partial_reconcile.id)
        self.assertFalse(je_ml.reconciled)
        self.assertFalse(invoice.tax_cash_basis_created_move_ids)

    def test_06_supplier_invoice_refund_reconcile(self):
        """Case on undue vat, to net refund with vendor bill.
        No cash basis entry, as there is no payment."""
        # Post suupplier invoice
        invoice = self.supplier_invoice_undue_vat.copy()
        invoice.invoice_date = invoice.date
        invoice.action_post()
        # Post supplier refund
        refund = self.supplier_refund_undue_vat.copy()
        refund.invoice_date = refund.date
        refund.action_post()
        # At invoice add refund to reconcile
        payable_account = refund.partner_id.property_account_payable_id
        refund_ml = refund.line_ids.filtered(
            lambda line: line.account_id == payable_account
        )
        invoice.js_assign_outstanding_line(refund_ml.id)
        # Standard creates undue VAT entries on payments only, not when
        # netting a bill with a refund
        self.assertTrue(refund_ml.reconciled)
        self.assertFalse(invoice.tax_cash_basis_created_move_ids)
        self.assertFalse(refund.tax_cash_basis_created_move_ids)

    def test_07_supplier_invoice_undue_refund_novat(self):
        """Case on undue vat bill, to net refund no vat with confirm.
        No cash basis entry, as there is no payment."""
        # Post suupplier invoice
        invoice = self.supplier_invoice_undue_vat.copy()
        invoice.invoice_date = invoice.date
        invoice.action_post()
        # Cash basis not create yet.
        self.assertFalse(invoice.tax_cash_basis_created_move_ids)

        # Add credit note without taxes
        ctx = {
            "active_ids": invoice.ids,
            "active_model": "account.move",
        }
        reversal_move = Form(
            self.env["account.move.reversal"].with_context(**ctx)
        ).save()
        action_reverse = reversal_move.refund_moves()
        reverse_move = self.env["account.move"].browse(action_reverse.get("res_id"))
        reverse_move.invoice_line_ids.write({"tax_ids": False})
        reverse_move.action_post()

        self.assertEqual(reverse_move.state, "posted")

        # Standard creates undue VAT entries on payments only, not when
        # netting a bill with a credit note
        self.assertFalse(invoice.tax_cash_basis_created_move_ids)
        reverse_move.button_draft()
        self.assertFalse(invoice.tax_cash_basis_created_move_ids)

    def test_08_supplier_invoice_reversal(self):
        """Case on reversal vendor bill."""
        # Post suupplier invoice
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today()
        self.supplier_invoice_vat.tax_invoice_ids.write(
            {"tax_invoice_number": tax_invoice, "tax_invoice_date": tax_date}
        )
        self.supplier_invoice_vat.action_post()
        # Add credit note
        reversal_model = self.env["account.move.reversal"].with_context(
            active_ids=self.supplier_invoice_vat.ids,
            active_model="account.move",
        )
        reversal_move = Form(reversal_model).save()
        # Can't reversal move, if not add tax number, date in account.move.reversal
        with self.assertRaises(UserError):
            reversal_move.modify_moves()  # reverse with new invoices
        tax_reversal_invoice = "RSINV-10001"
        reversal_move.write(
            {"tax_invoice_number": tax_reversal_invoice, "tax_invoice_date": tax_date}
        )
        reversal_move.modify_moves()
        self.assertEqual(self.supplier_invoice_vat.payment_state, "reversed")
        refund = self.supplier_invoice_vat.reversal_move_ids
        self.assertEqual(
            refund.tax_invoice_ids.tax_invoice_number, tax_reversal_invoice
        )
        self.assertEqual(refund.tax_invoice_ids.tax_invoice_date, tax_date)
        self.assertEqual(refund.tax_invoice_ids.tax_base_amount, -100)
        self.assertEqual(refund.tax_invoice_ids.balance, -7)
        new_bill = reversal_move.new_move_ids
        self.assertEqual(len(new_bill.tax_invoice_ids), 1)
        self.assertFalse(new_bill.tax_invoice_ids.tax_invoice_number)

        # A duplicate does not take the tax invoice of the reversal context
        duplicate = self.supplier_invoice_vat.with_context(
            tax_invoice_number="SHOULD-NOT-COPY",
            tax_invoice_date=fields.Date.today(),
        ).copy()
        self.assertEqual(duplicate.state, "draft")
        self.assertEqual(len(duplicate.tax_invoice_ids), 1)
        self.assertFalse(duplicate.tax_invoice_ids.tax_invoice_number)
        self.assertFalse(duplicate.tax_invoice_ids.tax_invoice_date)

    def test_09_supplier_invoice_zero_tax(self):
        """Case on 0% tax, Core odoo not create line with zero tax"""
        self.env.company.tax_zero_line = False
        invoice = self.supplier_invoice_zero_vat.copy()
        line_zero = invoice.line_ids.filtered(
            lambda line: not (line.debit or line.credit)
        )
        self.assertEqual(len(invoice.line_ids), 2)

        self.env.company.tax_zero_line = True
        invoice = self.supplier_invoice_zero_vat.copy()
        line_zero = invoice.line_ids.filtered(
            lambda line: not (line.debit or line.credit)
        )
        # There is 1 line for tax 0%
        self.assertEqual(len(invoice.line_ids), 3)
        self.assertTrue(line_zero)
        self.assertEqual(len(line_zero), 1)

        # Same for a sale 0% VAT, with its tax invoice
        zero_sale_vat = self._create_vat_tax(
            "Sale VAT 0%", "sale", 0, self.output_vat_acct
        )
        invoice = self._create_th_invoice(
            "out_invoice", [(1000, zero_sale_vat)], partner=self.partner
        )
        tax_line = invoice.line_ids.filtered(
            lambda line: line.tax_line_id == zero_sale_vat
        )
        self.assertEqual(len(tax_line), 1)
        self.assertEqual(tax_line.balance, 0)
        self.assertEqual(invoice.tax_invoice_ids.tax_base_amount, 1000)
        self.assertEqual(invoice.tax_invoice_ids.balance, 0)
        self.env.company.tax_zero_line = False
        invoice = self._create_th_invoice(
            "out_invoice", [(1000, zero_sale_vat)], partner=self.partner
        )
        self.assertFalse(
            invoice.line_ids.filtered(lambda line: line.tax_line_id == zero_sale_vat)
        )
        self.assertFalse(invoice.tax_invoice_ids)
        self.env.company.tax_zero_line = True

        # But not for a 0% withholding tax
        zero_wht = self._create_wht_tax("Purchase WHT 0%", amount=0)
        move = self._create_entry(
            [
                {
                    "name": "Zero withholding base",
                    "partner_id": self.partner.id,
                    "account_id": self.expense_account.id,
                    "debit": 1000,
                    "tax_ids": [Command.set(zero_wht.ids)],
                },
                {
                    "name": "Counterpart",
                    "account_id": self.payable_account.id,
                    "credit": 1000,
                },
            ],
            partner_id=self.partner.id,
        )
        self.assertFalse(
            move.line_ids.filtered(lambda line: line.tax_line_id == zero_wht)
        )
        self.assertFalse(move.tax_invoice_ids)
        move.action_post()
        self.assertEqual(move.state, "posted")

        # Nor for base lines without company, e.g. computed from a partner
        tax_model = self.env["account.tax"]
        for record in ({}, self.partner):
            base_line = tax_model._prepare_base_line_for_taxes_computation(
                record,
                price_unit=1000.0,
                quantity=1.0,
                tax_ids=self.input_zero_vat,
                currency_id=self.company.currency_id,
            )
            base_lines = [base_line]
            tax_model._add_tax_details_in_base_lines(base_lines, self.company)
            tax_model._round_base_lines_tax_details(base_lines, self.company)
            tax_model._add_accounting_data_in_base_lines_tax_details(
                base_lines, self.company
            )
            tax_data = base_line["tax_details"]["taxes_data"][0]
            self.assertEqual(base_line["tax_details"]["total_excluded_currency"], 1000)
            for tax_rep_data in tax_data["tax_reps_data"]:
                self.assertFalse(tax_rep_data["grouping_key"]["__keep_zero_line"])

        # The reversal of a 0% VAT entry reverses the tax base of its tax invoice
        move = self._create_tax_entry(
            self.input_zero_vat,
            [(self.partner, 1000.0)],
            journal=self.misc_journal,
            partner_id=self.partner.id,
        )
        origin_tax_invoice = move.tax_invoice_ids
        self.assertEqual(len(origin_tax_invoice), 1)
        tax_date = fields.Date.today()
        origin_tax_invoice.write(
            {"tax_invoice_number": "ZERO-REVERSAL-001", "tax_invoice_date": tax_date}
        )
        move.action_post()
        self.assertEqual(origin_tax_invoice.tax_base_amount, 1000)
        self.assertEqual(origin_tax_invoice.balance, 0)
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=move.ids)
            .create({"journal_id": move.journal_id.id, "date": tax_date})
        )
        wizard.refund_moves()
        reversal_tax_invoice = wizard.new_move_ids.tax_invoice_ids
        self.assertEqual(len(reversal_tax_invoice), 1)
        self.assertEqual(reversal_tax_invoice.tax_invoice_number, "ZERO-REVERSAL-001")
        self.assertEqual(reversal_tax_invoice.tax_base_amount, -1000)
        self.assertEqual(reversal_tax_invoice.balance, 0)
        self.assertEqual(origin_tax_invoice.tax_base_amount, 1000)

    def test_10_customer_invoice_vat(self):
        """Customer Invoice with VAT,
        system auto fill in Tax Invoice/Date on Invoice"""
        self.assertFalse(self.customer_invoice_vat.tax_invoice_ids.tax_invoice_number)
        self.customer_invoice_vat.action_post()
        tax_invoice = self.customer_invoice_vat.tax_invoice_ids
        self.assertEqual(tax_invoice.tax_invoice_number, self.customer_invoice_vat.name)
        self.assertEqual(tax_invoice.tax_invoice_date, self.customer_invoice_vat.date)
        self.assertEqual(tax_invoice.tax_base_amount, 100)
        self.assertEqual(tax_invoice.balance, 7)

        # A number entered by the user is kept, "/" is replaced
        invoice = self._create_th_invoice(
            "out_invoice", [(100, self.output_vat)], partner=self.partner
        )
        invoice.tax_invoice_ids.tax_invoice_number = "USER-ENTERED-001"
        invoice.action_post()
        self.assertEqual(invoice.tax_invoice_ids.tax_invoice_number, "USER-ENTERED-001")
        self.assertEqual(invoice.tax_invoice_ids.tax_invoice_date, invoice.date)
        invoice = self._create_th_invoice(
            "out_invoice", [(100, self.output_vat)], partner=self.partner
        )
        invoice.tax_invoice_ids.tax_invoice_number = "/"
        invoice.action_post()
        self.assertEqual(invoice.tax_invoice_ids.tax_invoice_number, invoice.name)
        self.assertEqual(invoice.tax_invoice_ids.tax_invoice_date, invoice.date)

        # A credit note uses its own number and date, with negative amounts
        tax_date = fields.Date.today() - relativedelta(days=1)
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "journal_id": invoice.journal_id.id,
                    "date": fields.Date.today(),
                    "tax_invoice_number": "IGNORED-CREDIT-NOTE-NUMBER",
                    "tax_invoice_date": tax_date,
                }
            )
        )
        wizard.refund_moves()
        refund = wizard.new_move_ids
        self.assertEqual(refund.move_type, "out_refund")
        refund.action_post()
        tax_invoice = refund.tax_invoice_ids
        self.assertEqual(tax_invoice.tax_invoice_number, refund.name)
        self.assertEqual(tax_invoice.tax_invoice_date, refund.date)
        self.assertEqual(tax_invoice.tax_base_amount, -100)
        self.assertEqual(tax_invoice.balance, -7)

    def test_11_customer_invoice_undue_vat(self):
        """Register Payment from Customer Invoice. The tax invoices of this module
        replace the standard Thai tax invoices, even for a VAT registered company,
        on invoice and on payment."""
        self.company.l10n_th_is_vat_registered = True

        self.customer_invoice_undue_vat.action_post()
        action = self.customer_invoice_undue_vat.action_register_payment()
        ctx = action.get("context")
        # Make full payment from invoice
        with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
        payment_wiz = f.save()
        res = payment_wiz.action_create_payments()
        payment = self.env["account.payment"].browse(res.get("res_id"))
        self.assertTrue(payment.tax_invoice_ids)
        self.assertIn(payment.state, ("paid", "reconciled"))
        tax_invoices = payment.tax_invoice_ids
        caba = payment.tax_invoice_move_ids
        self.assertEqual(caba.state, "posted")
        self.assertEqual(tax_invoices.payment_id, payment)
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        self.assertEqual(tax_invoice_number, payment.name)
        self.assertEqual(tax_invoices.tax_invoice_date, caba.date)
        self.assertEqual(tax_invoices.tax_base_amount, 100)
        self.assertEqual(tax_invoices.balance, 7)
        self.assertFalse(payment.to_clear_tax)
        # Check the move_line_ids, from both Bank and Cash Basis journal
        self.assertTrue(payment.move_id)
        self.assertTrue(payment.tax_invoice_move_ids)

        # No standard Thai tax invoice, also on reset, cancel and reverse
        StdTaxInvoice = self.env["l10n_th.tax.invoice"]
        invoices = self.customer_invoice_vat + self.customer_invoice_undue_vat
        self.customer_invoice_vat.action_post()
        self.assertTrue(self.customer_invoice_vat.tax_invoice_ids)
        self.assertFalse(invoices.l10n_th_tax_invoice_ids)
        self.assertFalse(StdTaxInvoice.search([("company_id", "=", self.company.id)]))
        payment.action_draft()
        payment.move_id.button_cancel()
        self.customer_invoice_vat.button_draft()
        self.customer_invoice_vat.button_cancel()
        self.assertFalse(StdTaxInvoice.search([("company_id", "=", self.company.id)]))
        # The VAT registration and the standard tab are hidden
        with Form(self.company) as company_form:
            self.assertTrue(
                company_form._get_modifier("l10n_th_is_vat_registered", "invisible")
            )
        with Form(self.customer_invoice_undue_vat) as move_form:
            self.assertTrue(
                move_form._get_modifier("l10n_th_tax_invoice_ids", "invisible")
            )

    def test_12_customer_invoice_vat_sequence(self):
        """Customer Invoice with VAT,
        system auto fill in Tax Invoice using sequence"""
        self.assertEqual(
            self.customer_invoice_vat_seq.company_id.customer_tax_invoice_number,
            "payment",
        )
        cust_inv_vat_doc = self.customer_invoice_vat_seq.copy()
        cust_inv_vat_doc.action_post()
        tax_invoices = cust_inv_vat_doc.tax_invoice_ids
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        # tax invoice number will auto fill following payment
        # This is not undue vat, so document there is value same as invoice
        self.assertEqual(tax_invoice_number, cust_inv_vat_doc.name)

        # Set customer tax invoice number = 'invoice'
        self.company.customer_tax_invoice_number = "invoice"
        self.assertEqual(
            self.customer_invoice_vat_seq.company_id.customer_tax_invoice_number,
            "invoice",
        )
        cust_inv_vat_doc_sequence_inv = self.customer_invoice_vat_seq.copy()
        cust_inv_vat_doc_sequence_inv.action_post()
        tax_invoices = cust_inv_vat_doc_sequence_inv.tax_invoice_ids
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        # tax invoice number will auto fill following invoice
        self.assertEqual(tax_invoice_number, cust_inv_vat_doc_sequence_inv.name)

        # Assign opptional sequence to vat
        self.cust_vat_sequence.prefix = "CTX"
        self.cust_vat_sequence.number_next_actual = 1  # CTX0001
        self.output_vat.taxinv_sequence_id = self.cust_vat_sequence
        self.customer_invoice_vat_seq.action_post()
        tax_invoices = self.customer_invoice_vat_seq.tax_invoice_ids
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        self.assertEqual(tax_invoice_number, "CTX0001")

        # Next number of the sequence, kept on reposting
        self.output_vat.sequence_number_next = 5
        self.assertEqual(self.output_vat.sequence_number_next, 5)
        invoice = self._create_th_invoice(
            "out_invoice", [(100, self.output_vat)], partner=self.partner, post=True
        )
        self.assertEqual(invoice.tax_invoice_ids.tax_invoice_number, "CTX0005")
        invoice.button_draft()
        invoice.action_post()
        self.assertEqual(invoice.tax_invoice_ids.tax_invoice_number, "CTX0005")

    def test_13_customer_invoice_undue_vat_sequence(self):
        """Register Payment from Customer Invoice
        system auto fill in Tax Invoice using sequence"""
        self.assertEqual(
            self.customer_invoice_undue_vat_seq.company_id.customer_tax_invoice_number,
            "payment",
        )
        cust_undue_doc = self.customer_invoice_undue_vat_seq.copy()
        cust_undue_doc.action_post()
        # Make full payment from invoice
        action = cust_undue_doc.action_register_payment()
        ctx = action.get("context")
        with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
        payment_wiz = f.save()
        res = payment_wiz.action_create_payments()
        payment = self.env["account.payment"].browse(res.get("res_id"))
        self.assertTrue(payment.tax_invoice_ids)
        self.assertIn(payment.state, ("paid", "reconciled"))
        tax_invoices = payment.tax_invoice_ids
        self.assertEqual(tax_invoices.payment_id, payment)
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        self.assertEqual(tax_invoice_number, payment.name)
        self.assertEqual(
            tax_invoices.tax_invoice_date, payment.tax_invoice_move_ids.date
        )
        self.assertEqual(payment.tax_invoice_move_ids.state, "posted")
        self.assertFalse(payment.to_clear_tax)

        # Set customer tax invoice number = 'invoice'
        self.company.customer_tax_invoice_number = "invoice"
        self.assertEqual(
            self.customer_invoice_undue_vat_seq.company_id.customer_tax_invoice_number,
            "invoice",
        )
        cust_undue_doc_seq_invoice = self.customer_invoice_undue_vat_seq.copy()
        cust_undue_doc_seq_invoice.action_post()
        # Make full payment from invoice
        action = cust_undue_doc_seq_invoice.action_register_payment()
        ctx = action.get("context")
        with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
        payment_wiz = f.save()
        res = payment_wiz.action_create_payments()
        payment = self.env["account.payment"].browse(res.get("res_id"))
        self.assertTrue(payment.tax_invoice_ids)
        self.assertIn(payment.state, ("paid", "reconciled"))
        tax_invoices = payment.tax_invoice_ids
        self.assertEqual(tax_invoices.payment_id, payment)
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        self.assertEqual(tax_invoice_number, cust_undue_doc_seq_invoice.name)
        self.assertEqual(
            tax_invoices.tax_invoice_date, payment.tax_invoice_move_ids.date
        )
        self.assertEqual(payment.tax_invoice_move_ids.state, "posted")
        self.assertFalse(payment.to_clear_tax)

        # Assign optional sequence to undue vat
        self.cust_vat_sequence.prefix = "CTX"
        self.cust_vat_sequence.number_next_actual = 2  # CTX0002
        self.undue_output_vat.taxinv_sequence_id = self.cust_vat_sequence
        self.assertEqual(self.undue_output_vat.sequence_number_next, 2)
        self.undue_output_vat.sequence_number_next = 5  # Change sequence number to 5
        # Do not allow user to fill in Tax Invoice/Date
        self.customer_invoice_undue_vat_seq.action_post()
        # Make full payment from invoice
        action = self.customer_invoice_undue_vat_seq.action_register_payment()
        ctx = action.get("context")
        with Form(self.env["account.payment.register"].with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
        payment_wiz = f.save()
        res = payment_wiz.action_create_payments()
        payment = self.env["account.payment"].browse(res.get("res_id"))
        self.assertTrue(payment.tax_invoice_ids)
        self.assertIn(payment.state, ("paid", "reconciled"))
        tax_invoices = payment.tax_invoice_ids
        self.assertEqual(tax_invoices.payment_id, payment)
        self.assertEqual(payment.tax_invoice_move_ids.state, "posted")
        tax_invoice_number = tax_invoices.mapped("tax_invoice_number")[0]
        self.assertEqual(tax_invoice_number, "CTX0005")
        self.assertEqual(
            tax_invoices.tax_invoice_date, payment.tax_invoice_move_ids.date
        )
        self.assertFalse(payment.to_clear_tax)
        # Check the move_line_ids, from both Bank and Cash Basis journal
        self.assertTrue(payment.move_id)
        self.assertTrue(payment.tax_invoice_move_ids)

    def test_14_included_tax(self):
        """
        Test an account.move.line is created automatically when adding a tax.
        This test uses the following scenario:
            - Create manually a debit line of 1000 having an included tax.
            - Assume a line containing the tax amount is created automatically.
            - Create manually a credit line to balance the two previous lines.
            - Save the move.

        included tax = 20%

        Name                   | Debit     | Credit    | Tax_ids  | Tax_line_id's name
        -----------------------|-----------|-----------|----------|-------------------
        debit_line_1           | 1000      |           | tax      |
        included_tax_line      | 200       |           |          | included_tax_line
        credit_line_1          |           | 1200      |          |
        """

        self.included_percent_tax = self.env["account.tax"].create(
            {
                "name": "included_tax_line",
                "amount_type": "percent",
                "amount": 20,
                "price_include": True,
                "include_base_amount": False,
            }
        )

        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "line_ids": [
                    Command.create(
                        {
                            "name": "debit_line_1",
                            "account_id": self.input_vat_acct.id,
                            "tax_ids": [Command.set(self.included_percent_tax.ids)],
                            "balance": 1000.0,  # debit
                        }
                    ),
                    Command.create(
                        {
                            "name": "credit_line_1",
                            "account_id": self.input_vat_acct.id,
                            "balance": -1200.0,  # credit
                        },
                    ),
                ],
            }
        )
        self.assertRecordValues(
            move.line_ids,
            [
                {
                    "name": "debit_line_1",
                    "debit": 1000.0,
                    "credit": 0.0,
                    "tax_ids": [self.included_percent_tax.id],
                    "tax_line_id": False,
                },
                {
                    "name": "credit_line_1",
                    "debit": 0.0,
                    "credit": 1200.0,
                    "tax_ids": [],
                    "tax_line_id": False,
                },
                {
                    "name": "included_tax_line",
                    "debit": 200.0,
                    "credit": 0.0,
                    "tax_ids": [],
                    "tax_line_id": self.included_percent_tax.id,
                },
            ],
        )

    def test_15_journal_entry_manual_tax(self):
        """Case manual tax in journal entry, purchase and sale journal entries"""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "line_ids": [
                    Command.create(
                        {
                            "name": "debit_line_1",
                            "account_id": self.input_vat_acct.id,
                            "balance": 1000.0,  # debit
                        }
                    ),
                    Command.create(
                        {
                            "name": "tax_line_1",
                            "account_id": self.input_vat_acct.id,
                            "balance": 200.0,  # debit
                        },
                    ),
                    Command.create(
                        {
                            "name": "credit_line_1",
                            "account_id": self.input_vat_acct.id,
                            "balance": -1200.0,  # credit
                        },
                    ),
                ],
            }
        )
        self.assertFalse(move.tax_invoice_ids)
        # Add tax manual in line tax
        line_tax = move.line_ids.filtered(lambda line: line.balance == 200.0)
        line_tax.manual_tax_invoice = True
        self.assertTrue(move.tax_invoice_ids)
        self.assertEqual(move.tax_invoice_ids.tax_base_amount, 0.0)
        self.assertEqual(move.tax_invoice_ids.balance, 200.0)
        today = fields.Date.today()
        move.tax_invoice_ids.tax_invoice_number = "TEST_TAX001"
        move.tax_invoice_ids.tax_invoice_date = today
        self.assertEqual(move.tax_invoice_ids.report_late_mo, "0")
        line_tax.manual_tax_invoice = False
        self.assertFalse(move.tax_invoice_ids)

        # Purchase VAT entered manually requires the vendor's tax invoice
        move = self._create_manual_vat_entry(manual_tax_invoice=False)
        vat_line = move.line_ids.filtered(
            lambda line: line.account_id == self.input_vat_acct and not line.tax_line_id
        )
        self.assertFalse(move.tax_invoice_ids)
        vat_line.manual_tax_invoice = True
        tax_invoice = vat_line.tax_invoice_ids
        self.assertEqual(len(tax_invoice), 1)
        self.assertEqual(tax_invoice.tax_base_amount, 0)
        self.assertEqual(tax_invoice.balance, 70)
        vat_line.manual_tax_invoice = True
        self.assertEqual(len(vat_line.tax_invoice_ids), 1)
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            move.action_post()
        tax_invoice.tax_invoice_number = "MANUAL-PURCHASE-001"
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            move.action_post()

        # Late report months follow the month difference, 6 months or more is 0
        move.date = fields.Date.to_date("2026-03-15")
        # (tax invoice date, report late, report date)
        for invoice_date, report_late, report_date in (
            # Same month
            ("2026-03-05", "0", "2026-03-05"),
            # One month before, same year
            ("2026-02-20", "1", "2026-03-31"),
            # Across the year boundary, 5 months is the latest late report
            ("2025-10-20", "5", "2026-03-31"),
            ("2025-12-31", "3", "2026-03-31"),
            # 6 months (2025-09 -> 2026-03) or more is not reportable as late
            ("2025-09-20", "0", "2025-09-20"),
            ("2025-09-01", "0", "2025-09-01"),
            ("2025-02-10", "0", "2025-02-10"),
            # Tax invoice date in a month after the accounting date
            ("2026-05-10", "0", "2026-05-10"),
        ):
            with Form(tax_invoice) as tax_inv:
                tax_inv.tax_invoice_date = fields.Date.to_date(invoice_date)
            self.assertEqual(tax_invoice.report_late_mo, report_late, invoice_date)
            self.assertEqual(
                tax_invoice.report_date, fields.Date.to_date(report_date), invoice_date
            )
        # Year boundary, accounting date in January
        move.date = fields.Date.to_date("2026-01-10")
        for invoice_date, report_late, report_date in (
            ("2025-12-15", "1", "2026-01-31"),
            ("2025-08-15", "5", "2026-01-31"),
            ("2025-07-31", "0", "2025-07-31"),
        ):
            with Form(tax_invoice) as tax_inv:
                tax_inv.tax_invoice_date = fields.Date.to_date(invoice_date)
            self.assertEqual(tax_invoice.report_late_mo, report_late, invoice_date)
            self.assertEqual(
                tax_invoice.report_date, fields.Date.to_date(report_date), invoice_date
            )
        move.action_post()
        self.assertEqual(move.state, "posted")
        # A duplicate is not a manual tax invoice
        duplicate = move.copy()
        duplicate_vat_line = duplicate.line_ids.filtered(
            lambda line: line.account_id == self.input_vat_acct and not line.tax_line_id
        )
        self.assertFalse(duplicate_vat_line.manual_tax_invoice)
        self.assertFalse(duplicate_vat_line.tax_invoice_ids)

        # Purchase VAT computed on a journal entry, with withholding tax
        move = self._create_entry(
            [
                {
                    "name": "Expense with VAT and WHT",
                    "partner_id": self.partner.id,
                    "account_id": self.expense_account.id,
                    "debit": 1000,
                    "tax_ids": [Command.set((self.input_vat | self.purchase_wht).ids)],
                },
                {
                    "name": "Payable",
                    "account_id": self.payable_account.id,
                    "credit": 1040,
                },
            ],
            partner_id=self.partner.id,
        )
        tax_invoice = move.tax_invoice_ids
        self.assertEqual(len(tax_invoice), 1)
        self.assertEqual(tax_invoice.tax_line_id, self.input_vat)
        wht_line = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.purchase_wht
        )
        self.assertEqual(len(wht_line), 1)
        self.assertFalse(wht_line.tax_invoice_ids)
        vat_line = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.input_vat
        )
        vat_line.manual_tax_invoice = True
        self.assertEqual(len(vat_line.tax_invoice_ids), 1)
        vat_line.manual_tax_invoice = False
        self.assertEqual(len(vat_line.tax_invoice_ids), 1)
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            move.action_post()
        tax_invoice.tax_invoice_number = "PURCHASE-JE-001"
        with self.assertRaisesRegex(
            UserError, "Please fill in tax invoice and tax date"
        ):
            move.action_post()
        tax_invoice.tax_invoice_date = fields.Date.today()
        move.action_post()
        self.assertEqual(move.state, "posted")

        # Sale VAT, computed or entered manually, numbered by the entry
        move = self._create_tax_entry(
            self.output_vat,
            [(self.partner, 1000.0)],
            journal=self.sale_journal,
            partner_id=self.partner.id,
        )
        tax_invoice = move.tax_invoice_ids
        self.assertEqual(len(tax_invoice), 1)
        tax_line = move.line_ids.filtered(
            lambda line: line.tax_line_id == self.output_vat
        )
        tax_line.manual_tax_invoice = True
        self.assertEqual(len(move.tax_invoice_ids), 1)
        tax_line.manual_tax_invoice = False
        self.assertEqual(len(move.tax_invoice_ids), 1)
        move.action_post()
        self.assertEqual(tax_invoice.tax_invoice_number, move.name)
        self.assertEqual(tax_invoice.tax_invoice_date, move.date)
        move = self._create_entry(
            [
                {
                    "name": "Receivable",
                    "partner_id": self.partner.id,
                    "account_id": self.receivable_account.id,
                    "debit": 1070,
                },
                {
                    "name": "Revenue",
                    "account_id": self.revenue_account.id,
                    "credit": 1000,
                },
                {
                    "name": "Manual output VAT",
                    "partner_id": self.partner.id,
                    "account_id": self.output_vat_acct.id,
                    "credit": 70,
                    "manual_tax_invoice": True,
                },
            ],
            journal=self.sale_journal,
            partner_id=self.partner.id,
        )
        tax_invoice = move.tax_invoice_ids
        self.assertEqual(len(tax_invoice), 1)
        self.assertEqual(tax_invoice.tax_base_amount, 0)
        self.assertEqual(tax_invoice.balance, 70)
        move.action_post()
        self.assertEqual(tax_invoice.tax_invoice_number, move.name)
        self.assertEqual(tax_invoice.tax_invoice_date, move.date)

    def test_16_reverse_journal_entry_auto_copy_tax_invoice(self):
        """Reverse journal entry without tax invoice fields in wizard should
        auto-copy tax invoice from original entry."""
        tax_invoice_number = "SINV/REV-001"
        tax_invoice_date = fields.Date.today()

        # Create a journal entry with manual tax invoice, then post
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    Command.create(
                        {
                            "name": "debit_line",
                            "account_id": self.input_vat_acct.id,
                            "balance": 1000.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": "tax_line",
                            "account_id": self.input_vat_acct.id,
                            "balance": 200.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": "credit_line",
                            "account_id": self.input_vat_acct.id,
                            "balance": -1200.0,
                        }
                    ),
                ],
            }
        )
        line_tax = move.line_ids.filtered(lambda line: line.balance == 200.0)
        line_tax.manual_tax_invoice = True
        move.tax_invoice_ids.write(
            {
                "tax_invoice_number": tax_invoice_number,
                "tax_invoice_date": tax_invoice_date,
            }
        )
        move.action_post()
        self.assertEqual(move.state, "posted")

        # Reverse via wizard, journal entry wizard has no tax fields
        reversal_model = self.env["account.move.reversal"].with_context(
            active_ids=move.ids,
            active_model="account.move",
        )
        reversal_move = Form(reversal_model).save()
        # tax invoice number/date are auto-copied from original
        reversal_move.modify_moves()

        # Verify reversed move has tax invoice copied from original
        reversed_move = self.env["account.move"].search(
            [("reversed_entry_id", "=", move.id)]
        )
        self.assertTrue(reversed_move)
        self.assertEqual(
            reversed_move.tax_invoice_ids.tax_invoice_number,
            tax_invoice_number,
        )
        self.assertEqual(
            reversed_move.tax_invoice_ids.tax_invoice_date, tax_invoice_date
        )
        self.assertEqual(reversed_move.tax_invoice_ids.reversed_id, move)
        self.assertEqual(move.tax_invoice_ids.reversing_id, reversed_move)
        self.assertEqual(reversed_move.tax_invoice_ids.tax_base_amount, 0)
        self.assertEqual(reversed_move.tax_invoice_ids.balance, -200)

        # Same for a purchase VAT computed on the entry
        move = self._create_tax_entry(
            self.input_vat,
            [(self.partner, 1000.0)],
            journal=self.misc_journal,
            partner_id=self.partner.id,
        )
        origin_tax_invoice = move.tax_invoice_ids
        tax_date = fields.Date.today()
        origin_tax_invoice.write(
            {"tax_invoice_number": "MANUAL-REVERSAL-001", "tax_invoice_date": tax_date}
        )
        move.action_post()
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=move.ids)
            .create({"journal_id": move.journal_id.id, "date": tax_date})
        )
        wizard.refund_moves()
        reversal = wizard.new_move_ids
        reversal_tax_invoice = reversal.tax_invoice_ids
        self.assertEqual(reversal.reversed_entry_id, move)
        self.assertEqual(len(reversal_tax_invoice), 1)
        self.assertEqual(reversal_tax_invoice.tax_invoice_number, "MANUAL-REVERSAL-001")
        self.assertEqual(reversal_tax_invoice.tax_invoice_date, tax_date)
        self.assertEqual(reversal_tax_invoice.reversed_id, move)
        self.assertEqual(origin_tax_invoice.reversing_id, reversal)
        self.assertEqual(reversal_tax_invoice.tax_base_amount, -1000)
        self.assertEqual(reversal_tax_invoice.balance, -70)

        # Reversing a sales entry does not consume a number of the sequence
        sequence = self.env["ir.sequence"].create(
            {"name": "JE Reversal VAT Sequence", "prefix": "JEREV", "padding": 4}
        )
        self.output_vat.taxinv_sequence_id = sequence
        sequence.invalidate_recordset(["number_next_actual"])
        self.assertEqual(sequence.number_next_actual, 1)
        journal = self.sale_journal
        entry_date = fields.Date.to_date("2026-03-10")
        move = self._create_entry(
            [
                {
                    "name": "Receivable",
                    "partner_id": self.partner.id,
                    "account_id": self.receivable_account.id,
                    "debit": 1070.0,
                },
                {
                    "name": "Taxable revenue",
                    "partner_id": self.partner.id,
                    "account_id": self.revenue_account.id,
                    "credit": 1000.0,
                    "tax_ids": [Command.set(self.output_vat.ids)],
                },
            ],
            journal=journal,
            date=entry_date,
            partner_id=self.partner.id,
        )
        tax_invoice = move.tax_invoice_ids
        self.assertEqual(len(tax_invoice), 1)
        self.assertIn(tax_invoice.tax_invoice_number, (False, "/"))

        move.action_post()
        self.assertEqual(tax_invoice.tax_invoice_number, "JEREV0001")
        self.assertEqual(tax_invoice.tax_invoice_date, entry_date)
        self.assertEqual(tax_invoice.tax_base_amount, 1000)
        self.assertEqual(tax_invoice.balance, 70)
        sequence.invalidate_recordset(["number_next_actual"])
        self.assertEqual(sequence.number_next_actual, 2)

        reversal_date = fields.Date.to_date("2026-03-20")
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=move.ids)
            .create({"journal_id": journal.id, "date": reversal_date})
        )
        wizard.refund_moves()
        reversal = wizard.new_move_ids
        self.assertEqual(reversal.reversed_entry_id, move)
        self.assertEqual(reversal.state, "posted")
        reversal_tax_invoice = reversal.tax_invoice_ids
        self.assertEqual(len(reversal_tax_invoice), 1)
        # Same number as the origin, no new number from the sequence
        self.assertEqual(reversal_tax_invoice.tax_invoice_number, "JEREV0001")
        self.assertEqual(reversal_tax_invoice.tax_invoice_date, reversal_date)
        self.assertEqual(reversal_tax_invoice.reversed_id, move)
        self.assertEqual(tax_invoice.reversing_id, reversal)
        self.assertEqual(reversal_tax_invoice.tax_base_amount, -1000)
        self.assertEqual(reversal_tax_invoice.balance, -70)
        sequence.invalidate_recordset(["number_next_actual"])
        self.assertEqual(sequence.number_next_actual, 2)

        # The next sales entry gets the next number
        next_move = move.copy({"date": reversal_date})
        next_move.action_post()
        self.assertEqual(next_move.tax_invoice_ids.tax_invoice_number, "JEREV0002")
        sequence.invalidate_recordset(["number_next_actual"])
        self.assertEqual(sequence.number_next_actual, 3)

    def test_17_no_tax_invoice_for_non_thai_company(self):
        """Tax invoices are for Thai companies only, a vendor bill of another
        company is posted without tax invoice number and date."""
        company_data = self.setup_other_company(
            name="US Company", country_id=self.env.ref("base.us").id
        )
        company = company_data["company"]
        AccountMove = self.env["account.move"].with_company(company)
        for move_type, tax in (
            ("out_invoice", company_data["default_tax_sale"]),
            ("in_invoice", company_data["default_tax_purchase"]),
        ):
            move = AccountMove.create(
                {
                    "move_type": move_type,
                    "partner_id": self.partner.id,
                    "invoice_date": fields.Date.today(),
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "Test line",
                                "price_unit": 1000.0,
                                "tax_ids": [Command.set(tax.ids)],
                            }
                        )
                    ],
                }
            )
            self.assertTrue(move.line_ids.filtered("tax_line_id"))
            move.action_post()
            self.assertEqual(move.state, "posted")
            self.assertFalse(move.tax_invoice_ids)
        # Manual tax invoice, on create and on write
        entry = AccountMove.create(
            {
                "move_type": "entry",
                "journal_id": company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {
                            "name": "VAT",
                            "account_id": company_data["default_account_expense"].id,
                            "debit": 70.0,
                            "manual_tax_invoice": True,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Payable",
                            "account_id": company_data["default_account_payable"].id,
                            "credit": 70.0,
                        }
                    ),
                ],
            }
        )
        self.assertFalse(entry.tax_invoice_ids)
        entry.line_ids[1].manual_tax_invoice = True
        self.assertFalse(entry.tax_invoice_ids)
        entry.action_post()
        self.assertEqual(entry.state, "posted")
