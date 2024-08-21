# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.account_invoice_inter_company.tests.test_inter_company_invoice import (
    TestAccountInvoiceInterCompanyBase,
)


class TestTaxInvoiceInterCompany(TestAccountInvoiceInterCompanyBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice_company_b = Form(
            cls.account_move_obj.with_company(cls.company_b.id).with_context(
                default_move_type="in_invoice",
            )
        )
        cls.invoice_company_b.partner_id = cls.partner_company_a
        cls.invoice_company_b.journal_id = cls.purchases_journal_company_b
        cls.invoice_company_b.currency_id = cls.env.ref("base.EUR")
        cls.invoice_company_b.invoice_date = fields.Date.today()

        with cls.invoice_company_b.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_consultant_multi_company
            line_form.quantity = 1
            line_form.product_uom_id = cls.env.ref("uom.product_uom_hour")
            line_form.account_id = cls.a_sale_company_b
            line_form.name = "Service Multi Company"
            line_form.price_unit = 450.0
        cls.invoice_company_b = cls.invoice_company_b.save()
        cls.invoice_line_a = cls.invoice_company_b.invoice_line_ids[0]

    def test_01_invoice_vat_inter_company(self):
        """
        Test case for validating the creation of a tax invoice in an inter-company scenario.

        This test verifies the following steps:
        1. Check that the move type of the invoice in company A is 'out_invoice'.
        2. Ensure that the invoice in company A has at least one tax invoice associated with it.
        3. Confirm the invoice in company A.
        4. Search for the destination invoice created in
            company B based on the auto_invoice_id field.
        5. Check that only one destination invoice is found.
        6. Verify that the move type of the destination invoice in company B is 'in_invoice'.
        7. Compare the tax invoice numbers / dates of the destination invoice in
            company B with the tax invoice numbers / dates of the source invoice in company A.
        """
        self.assertEqual(self.invoice_company_a.move_type, "out_invoice")
        self.assertTrue(self.invoice_company_a.tax_invoice_ids)
        # Confirm the invoice of company A
        self.invoice_company_a.with_user(self.user_company_a.id).action_post()
        # Check destination invoice created in company B
        invoice_company_b = self.account_move_obj.with_user(
            self.user_company_b.id
        ).search([("auto_invoice_id", "=", self.invoice_company_a.id)])
        self.assertEqual(len(invoice_company_b), 1)
        self.assertEqual(invoice_company_b.move_type, "in_invoice")
        self.assertEqual(
            invoice_company_b.tax_invoice_ids.mapped("tax_invoice_number"),
            self.invoice_company_a.tax_invoice_ids.mapped("tax_invoice_number"),
        )
        self.assertEqual(
            invoice_company_b.tax_invoice_ids.mapped("tax_invoice_date"),
            self.invoice_company_a.tax_invoice_ids.mapped("tax_invoice_date"),
        )

    def test_02_bill_vat_inter_company(self):
        """
        Test case for bill VAT between inter-company transactions.

        This test verifies the following steps:
        1. Checks that the move type of the invoice is "in_invoice".
        2. Raises a UserError when trying to post the invoice without
            filling in the tax invoice and tax date.
        3. Updates the tax invoice and tax date of the invoice.
        4. Posts the invoice.
        5. Checks that a destination invoice is created in company B.
        6. Verifies that the tax invoice number and tax invoice date of the destination invoice
            are different from the source invoice.
        """
        self.assertEqual(self.invoice_company_b.move_type, "in_invoice")
        with self.assertRaises(UserError) as e:
            self.invoice_company_b.with_user(self.user_company_b.id).action_post()
        self.assertEqual(e.exception.args[0], "Please fill in tax invoice and tax date")
        # Update tax invoice
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today() + timedelta(days=5)
        self.invoice_company_b.tax_invoice_ids.write(
            {
                "tax_invoice_number": tax_invoice,
                "tax_invoice_date": tax_date,
            }
        )
        self.invoice_company_b.with_user(self.user_company_b.id).action_post()
        # Check destination invoice created in company B
        invoice_company_a = self.account_move_obj.with_user(
            self.user_company_a.id
        ).search([("auto_invoice_id", "=", self.invoice_company_b.id)])
        self.assertEqual(len(invoice_company_a), 1)
        self.assertEqual(invoice_company_a.move_type, "out_invoice")
        # Tax invoice must use standard sequence
        self.assertNotEqual(
            invoice_company_a.tax_invoice_ids.mapped("tax_invoice_number"),
            self.invoice_company_b.tax_invoice_ids.mapped("tax_invoice_number"),
        )
        self.assertNotEqual(
            invoice_company_a.tax_invoice_ids.mapped("tax_invoice_date"),
            self.invoice_company_b.tax_invoice_ids.mapped("tax_invoice_date"),
        )
