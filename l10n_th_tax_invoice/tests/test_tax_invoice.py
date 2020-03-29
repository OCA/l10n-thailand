# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import SingleTransactionCase


class TestTaxInvoice(SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestTaxInvoice, cls).setUpClass()
        Journal = cls.env["account.journal"]
        # Setup company to allow using tax cash basis
        cls.journal_undue = cls.env["account.journal"].create(
            {"name": "UndueVAT", "type": "general", "code": "UNDUE"}
        )
        company = cls.env.ref("base.main_company")
        company.write(
            {"tax_exigibility": True, "tax_cash_basis_journal_id": cls.journal_undue.id}
        )
        type_current_asset = cls.env.ref("account.data_account_type_current_assets")
        type_current_liability = cls.env.ref(
            "account.data_account_type_current_liabilities"
        )
        # Journals
        cls.journal_purchase = Journal.search([("type", "=", "purchase")])[0]
        cls.journal_sale = Journal.search([("type", "=", "sale")])[0]
        cls.journal_bank = Journal.search([("type", "=", "bank")])[0]
        # Payment Methods
        cls.payment_method_manual_out = cls.env.ref(
            "account.account_payment_method_manual_out"
        )
        # Accounts
        cls.output_vat_acct = cls.env["account.account"].create(
            {"name": "O7", "code": "O7", "user_type_id": type_current_liability.id}
        )
        cls.undue_output_vat_acct = cls.env["account.account"].create(
            {"name": "DO7", "code": "DO7", "user_type_id": type_current_asset.id}
        )
        cls.input_vat_acct = cls.env["account.account"].create(
            {"name": "V7", "code": "V7", "user_type_id": type_current_liability.id}
        )
        cls.undue_input_vat_acct = cls.env["account.account"].create(
            {"name": "DV7", "code": "DV7", "user_type_id": type_current_asset.id}
        )
        # Tax Group
        cls.tax_group_undue_vat = cls.env["account.tax.group"].create(
            {"name": "UndueVAT"}
        )
        cls.tax_group_vat = cls.env["account.tax.group"].create({"name": "VAT"})
        # Tax
        cls.output_vat = cls.env["account.tax"].create(
            {
                "name": "O7",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 7.0,
                "tax_group_id": cls.tax_group_vat.id,
                "tax_exigibility": "on_invoice",
                "invoice_repartition_line_ids": [
                    (0, 0, {"factor_percent": 100.0, "repartition_type": "base"}),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.output_vat_acct.id,
                        },
                    ),
                ],
            }
        )
        cls.undue_output_vat = cls.env["account.tax"].create(
            {
                "name": "DO7",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 7.0,
                "tax_group_id": cls.tax_group_undue_vat.id,
                "tax_exigibility": "on_payment",
                "invoice_repartition_line_ids": [
                    (0, 0, {"factor_percent": 100.0, "repartition_type": "base"}),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.output_vat_acct.id,
                        },
                    ),
                ],
                "cash_basis_transition_account_id": cls.undue_output_vat_acct.id,
                "cash_basis_base_account_id": cls.output_vat_acct.id,
            }
        )
        cls.input_vat = cls.env["account.tax"].create(
            {
                "name": "V7",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 7.0,
                "tax_group_id": cls.tax_group_vat.id,
                "tax_exigibility": "on_invoice",
                "invoice_repartition_line_ids": [
                    (0, 0, {"factor_percent": 100.0, "repartition_type": "base"}),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.input_vat_acct.id,
                        },
                    ),
                ],
            }
        )
        cls.undue_input_vat = cls.env["account.tax"].create(
            {
                "name": "DV7",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 7.0,
                "tax_group_id": cls.tax_group_undue_vat.id,
                "tax_exigibility": "on_payment",
                "invoice_repartition_line_ids": [
                    (0, 0, {"factor_percent": 100.0, "repartition_type": "base"}),
                    (
                        0,
                        0,
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.input_vat_acct.id,
                        },
                    ),
                ],
                "cash_basis_transition_account_id": cls.undue_input_vat_acct.id,
                "cash_basis_base_account_id": cls.input_vat_acct.id,
            }
        )
        cls.payment_term_immediate = cls.env["account.payment.term"].create(
            {"name": "", "line_ids": [(0, 0, {"value": "balance", "days": 15})]}
        )
        # Prepare Supplier Invoices
        invoice_dict = {
            "name": "Test Supplier Invoice VAT",
            "partner_id": cls.env.ref("base.res_partner_12").id,
            "journal_id": cls.journal_purchase.id,
            "type": "in_invoice",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "quantity": 1.0,
                        "account_id": cls.env["account.account"]
                        .search(
                            [
                                (
                                    "user_type_id",
                                    "=",
                                    cls.env.ref(
                                        "account.data_account_type_expenses"
                                    ).id,
                                )
                            ],
                            limit=1,
                        )
                        .id,
                        "name": "Advice",
                        "price_unit": 100.00,
                        "tax_ids": [(6, 0, [cls.input_vat.id])],
                    },
                )
            ],
        }
        cls.supplier_invoice_vat = cls.env["account.move"].create(invoice_dict)
        # Supplier Invoice Undue VAT
        invoice_dict = {
            "name": "Test Supplier Invoice UndueVAT",
            "partner_id": cls.env.ref("base.res_partner_10").id,
            "journal_id": cls.journal_purchase.id,
            "type": "in_invoice",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "quantity": 1.0,
                        "account_id": cls.env["account.account"]
                        .search(
                            [
                                (
                                    "user_type_id",
                                    "=",
                                    cls.env.ref(
                                        "account.data_account_type_expenses"
                                    ).id,
                                )
                            ],
                            limit=1,
                        )
                        .id,
                        "name": "Advice",
                        "price_unit": 100.00,
                        "tax_ids": [(6, 0, [cls.undue_input_vat.id])],
                    },
                )
            ],
        }
        cls.supplier_invoice_undue_vat = cls.env["account.move"].create(invoice_dict)

    def test_supplier_invoice_vat(self):
        """ Supplier Invoice with VAT,
        user must fill in Tax Invoice/Date on Invoice """
        # User have not filled in Tax Invoice / Date in account_invoice_tax
        with self.assertRaises(UserError) as e:
            self.supplier_invoice_vat.action_post()
        self.assertEqual(e.exception.name, "Please fill in tax invoice and tax date")
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today()
        self.supplier_invoice_vat.tax_invoice_ids.write(
            {"tax_invoice_number": tax_invoice, "tax_invoice_date": tax_date}
        )
        self.supplier_invoice_vat.action_post()

    def test_supplier_invoice_undue_vat_payment(self):
        """ Register Payment from Vendor Invoice"""
        # Do not allow user to fill in Tax Invoice/Date
        tax_invoice = "SINV-10001"
        tax_date = fields.Date.today()
        self.supplier_invoice_undue_vat.action_post()
        # Make full payment from invoice
        payment = self.env["account.payment"].create(
            {
                "payment_date": fields.Date.today(),
                "payment_type": "outbound",
                "amount": 107.00,
                "journal_id": self.journal_bank.id,
                "partner_type": "supplier",
                "partner_id": self.env.ref("base.res_partner_10").id,
                "payment_method_id": self.payment_method_manual_out.id,
                "invoice_ids": [(4, self.supplier_invoice_undue_vat.id, None)],
            }
        )
        payment.post()
        self.assertTrue(payment.tax_invoice_ids)
        # Clear tax cash basis
        with self.assertRaises(UserError) as e:
            payment.clear_tax_cash_basis()
        self.assertEqual(e.exception.name, "Please fill in tax invoice and tax date")
        # Fill in tax invoice and clear undue vat
        payment.tax_invoice_ids.write(
            {"tax_invoice_number": tax_invoice, "tax_invoice_date": tax_date}
        )
        payment.clear_tax_cash_basis()
        # Cash basis journal is now posted
        self.assertEquals(payment.tax_invoice_ids.mapped("move_id").state, "posted")
        # Check the move_line_ids, from both Bank and Cash Basis journal
        self.assertEquals(len(payment.move_line_ids.mapped("move_id")), 2)
        payment.action_draft()  # Unlink the relation
        self.assertFalse(payment.move_line_ids)
