# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged

from .test_tax_invoice import TestTaxInvoice


@tagged("post_install", "-at_install")
class TestReverseTaxes(TestTaxInvoice):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.output_vat.refund_repartition_line_ids.filtered(
            lambda rep: rep.repartition_type == "tax"
        ).account_id = cls.output_vat_acct
        cls.undue_output_vat.reverse_tax_id = cls.output_vat

    def _register_payment(self, invoice, amount=None):
        action = invoice.action_register_payment()
        ctx = action.get("context")
        vals = {"journal_id": self.journal_bank.id}
        if amount is not None:
            vals["amount"] = amount
        wizard = self.env["account.payment.register"].with_context(**ctx).create(vals)
        wizard.action_create_payments()
        return invoice

    def _new_reversal(self, invoice):
        return (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({"journal_id": invoice.journal_id.id})
        )

    def _tax_by_account(self, move):
        result = {}
        for line in move.line_ids.filtered("tax_line_id"):
            result.setdefault(line.account_id, 0.0)
            result[line.account_id] += abs(line.balance)
        return result

    def test_01_credit_note_full_paid_uses_due_tax(self):
        """Fully paid invoice -> credit note books VAT to due account."""
        invoice = self.customer_invoice_undue_vat
        invoice.action_post()
        self._register_payment(invoice)
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))

        wizard = self._new_reversal(invoice)
        self.assertTrue(wizard.show_reverse_taxes)
        self.assertTrue(wizard.use_reverse_taxes)
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        refund.action_post()

        tax_by_account = self._tax_by_account(refund)
        # All 7.0 VAT on the due account, nothing on the undue/suspense account
        self.assertEqual(tax_by_account.get(self.output_vat_acct), 7.0)
        self.assertNotIn(self.undue_output_vat_acct, tax_by_account)
        self.assertEqual(sum(refund.invoice_line_ids.mapped("price_subtotal")), 100.0)

    def test_03_no_mapping_keeps_undue(self):
        """Without reverse_tax_id, behaviour is unchanged (undue account)."""
        self.undue_output_vat.reverse_tax_id = False
        invoice = self.customer_invoice_undue_vat
        invoice.action_post()
        self._register_payment(invoice)

        wizard = self._new_reversal(invoice)
        self.assertFalse(wizard.show_reverse_taxes)
        self.assertFalse(wizard.use_reverse_taxes)
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        refund.action_post()

        tax_by_account = self._tax_by_account(refund)
        # VAT stays on the undue/suspense account
        self.assertEqual(tax_by_account.get(self.undue_output_vat_acct), 7.0)
        self.assertNotIn(self.output_vat_acct, tax_by_account)
