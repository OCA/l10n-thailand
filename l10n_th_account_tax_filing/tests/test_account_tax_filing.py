# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


import datetime

from dateutil.rrule import MONTHLY
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountTaxFiling(TransactionCase):
    @classmethod
    @freeze_time("2025-01-01")
    def setUpClass(cls):
        super().setUpClass()

        # Create date range
        cls.date_range_obj = cls.env["date.range"]
        cls._create_date_range(cls)
        cls.date_range = cls.date_range_obj.search([], limit=1, order="date_start asc")
        cls.first_date_range = cls.date_range_obj.search(
            [], limit=1, order="date_start"
        )

        cls.account_tax_filing = cls.env["account.tax.filing"]
        Journal = cls.env["account.journal"]

        # Journals
        cls.journal_purchase = Journal.search([("type", "=", "purchase")])[0]
        cls.journal_sale = Journal.search([("type", "=", "sale")])[0]

        # account_type
        type_current_asset = cls.env.ref("account.data_account_type_current_assets")
        type_current_liability = cls.env.ref(
            "account.data_account_type_current_liabilities"
        )

        # Sales tax (Account From)
        cls.output_vat_acct = cls.env["account.account"].create(
            {"name": "OutVat", "code": "100", "user_type_id": type_current_liability.id}
        )
        # Purchase tax (Account To)
        cls.input_vat_acct = cls.env["account.account"].create(
            {"name": "InVat", "code": "200", "user_type_id": type_current_asset.id}
        )
        # Adjust Tax (Tax Receivable)
        cls.adjust_acct = cls.env["account.account"].create(
            {
                "name": "Adjusts Vat",
                "code": "101",
                "user_type_id": type_current_liability.id,
            }
        )
        # Tax Group
        cls.tax_group_vat = cls.env["account.tax.group"].create({"name": "VAT"})

        cls.output_vat = cls.env["account.tax"].create(
            {
                "name": "Output Vat 7%",
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
        cls.input_vat = cls.env["account.tax"].create(
            {
                "name": "Input Vat 7%",
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

    def _create_date_range(self):
        RangeType = self.env["date.range.type"]
        Generator = self.env["date.range.generator"]
        range_type = RangeType.create({"name": "Period"})
        year = datetime.datetime.now().year
        generator = Generator.create(
            {
                "name_prefix": "{}-".format(year),
                "duration_count": 1,
                "unit_of_time": str(MONTHLY),
                "count": 12,
                "type_id": range_type.id,
                "date_start": "{}-01-01".format(year),
            }
        )
        generator.action_apply()

    @freeze_time("2025-01-01")
    def _create_invoice(
        self, name, partner, journal, invoice_type, account_type, price, vat
    ):
        invoice_dict = {
            "name": name,
            "partner_id": partner.id,
            "journal_id": journal.id,
            "move_type": invoice_type,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "quantity": 1.0,
                        "account_id": self.env["account.account"]
                        .search(
                            [
                                ("user_type_id", "=", account_type.id),
                                ("company_id", "=", 1),
                            ],
                            limit=1,
                        )
                        .id,
                        "name": "Advice",
                        "price_unit": price,
                        "tax_ids": [(6, 0, [vat.id])],
                    },
                )
            ],
        }
        return self.env["account.move"].create(invoice_dict)

    def _create_account_tax_filing(self, adjust_acct=None):
        tax_filing_dict = {
            "name": "Draft",
            "partner_id": self.env.ref("base.res_partner_10").id,
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "account_from_id": self.output_vat_acct.id,
            "account_to_id": self.input_vat_acct.id,
            "account_adjust_id": adjust_acct.id if adjust_acct else False,
        }
        return self.env["account.tax.filing"].create(tax_filing_dict)

    @freeze_time("2025-01-01")
    def create_account_tax_filing(self, adjust_acct=None):
        tax_filing = self._create_account_tax_filing(adjust_acct)
        tax_filing.action_compute_account_tax_filing_line()
        tax_filing.action_submit()
        tax_filing.action_create_invoice()
        return tax_filing

    def create_invoice(self, amount, index=1):
        # Prepare Customer Invoices
        customer_invoice = self._create_invoice(
            f"Test{index} Customer Invoice VAT",
            self.env.ref("base.res_partner_10"),
            self.journal_sale,
            "out_invoice",
            self.env.ref("account.data_account_type_revenue"),
            amount,
            self.output_vat,
        )
        customer_invoice.action_post()
        return customer_invoice

    def create_bill(self, amount, index=1):
        # Prepare Supplier Invoices
        supplier_invoice = self._create_invoice(
            f"Test{index} Supplier Invoice VAT",
            self.env.ref("base.res_partner_12"),
            self.journal_purchase,
            "in_invoice",
            self.env.ref("account.data_account_type_expenses"),
            amount,
            self.input_vat,
        )
        tax_invoice = "SINV-10001"
        tax_date = "2025-01-01"
        supplier_invoice.tax_invoice_ids.write(
            {"tax_invoice_number": tax_invoice, "tax_invoice_date": tax_date}
        )
        supplier_invoice.action_post()
        return supplier_invoice

    def test_01_create_invoice(self):
        self.create_invoice(100)
        self.create_bill(200)
        tax_filing = self.create_account_tax_filing()
        self.assertEqual(tax_filing.total_amount, 7.0)
        self.assertEqual(tax_filing.move_id.move_type, "out_invoice")
        self.assertEqual(tax_filing.move_id.amount_total, 7.0)

    def test_02_create_vendor_bill(self):
        self.create_invoice(200)
        self.create_bill(100)
        tax_filing = self.create_account_tax_filing()
        self.assertEqual(tax_filing.total_amount, -7.0)
        self.assertEqual(tax_filing.move_id.move_type, "in_invoice")
        self.assertEqual(tax_filing.move_id.amount_total, 7.0)

    def test_03_create_journal_entries(self):
        self.create_invoice(100)
        self.create_bill(100)
        tax_filing = self.create_account_tax_filing()
        self.assertEqual(tax_filing.total_amount, 0.0)
        self.assertEqual(tax_filing.move_id.move_type, "entry")

    def test_04_create_vendor_bill_none_adjust_line(self):
        self.create_invoice(200)
        self.create_bill(100)
        tax_filing = self.create_account_tax_filing(self.adjust_acct)
        self.assertEqual(tax_filing.total_amount, -7.0)
        self.assertEqual(tax_filing.move_id.move_type, "in_invoice")
        self.assertEqual(tax_filing.move_id.amount_total, 7.0)

    def test_05_create_vendor_bill_has_adjust_line(self):
        # Create Adjust Line
        invoice_1 = self.create_invoice(100)
        bill_1 = self.create_bill(200)
        tax_filing = self.create_account_tax_filing(self.adjust_acct)
        tax_filing.move_id.action_post()
        self.assertEqual(tax_filing.total_amount, 7.0)
        self.assertEqual(tax_filing.move_id.move_type, "entry")
        invoice_1.button_draft()
        bill_1.button_draft()

        # Account Tax Filing has adjust line
        # Prepare Customer Invoices
        customer_invoice1 = self._create_invoice(
            "Test2 Customer Invoice VAT",
            self.env.ref("base.res_partner_10"),
            self.journal_sale,
            "out_invoice",
            self.env.ref("account.data_account_type_revenue"),
            200.00,
            self.output_vat,
        )
        customer_invoice1.action_post()
        tax_filing1 = self.create_account_tax_filing(self.adjust_acct)
        self.assertEqual(tax_filing1.total_amount, -7.0)
        self.assertEqual(tax_filing1.move_id.move_type, "in_invoice")
        self.assertEqual(tax_filing1.move_id.amount_total, 7.0)

    def test_06_create_journal_entries_has_adjust(self):
        # Create Adjust Line 1
        invoice_1 = self.create_invoice(100)
        bill_1 = self.create_bill(200)
        tax_filing1 = self.create_account_tax_filing(self.adjust_acct)
        tax_filing1.move_id.action_post()
        self.assertEqual(tax_filing1.total_amount, 7.0)
        self.assertEqual(tax_filing1.move_id.move_type, "entry")
        invoice_1.button_draft()
        bill_1.button_draft()

        # Create Adjust Line 2
        invoice_2 = self.create_invoice(100, 2)
        bill_2 = self.create_bill(200, 2)
        tax_filing2 = self.create_account_tax_filing(self.adjust_acct)
        tax_filing2.move_id.action_post()
        self.assertEqual(tax_filing2.total_amount, 14.0)
        self.assertEqual(tax_filing2.move_id.move_type, "entry")
        tax_filing1.move_id.button_draft()
        invoice_2.button_draft()
        bill_2.button_draft()

        # Account Tax Filing has adjust line
        # Prepare Customer Invoices
        self.create_invoice(100, 3)
        tax_filing3 = self.create_account_tax_filing(self.adjust_acct)
        self.assertEqual(tax_filing3.total_amount, 7.0)
        self.assertEqual(tax_filing3.move_id.move_type, "entry")

    def test_07_check_submit_without_line_and_cancel_tax_filing(self):
        # Create Adjust Line 1
        self.create_invoice(100)
        self.create_bill(200)
        tax_filing1 = self._create_account_tax_filing(self.adjust_acct)
        tax_filing1.date_range_id = self.first_date_range
        with self.assertRaises(UserError):
            tax_filing1.action_submit()
        with self.assertRaises(UserError):
            tax_filing1.action_create_invoice()
        with self.assertRaises(UserError):
            tax_filing1.date_from = "2025-02-01"
        tax_filing1.action_compute_account_tax_filing_line()
        tax_filing1.action_submit()
        tax_filing1.action_draft()
        tax_filing1.action_cancel()
        self.assertEqual(tax_filing1.total_amount, 7.0)
        tax_filing2 = self.create_account_tax_filing(self.adjust_acct)
        tax_filing2.action_view_entries()
        self.assertEqual(tax_filing2.total_amount, 7.0)
        self.assertEqual(tax_filing2.move_id.move_type, "entry")
        self.assertEqual(tax_filing2.account_from_id.id, self.output_vat_acct.id)
        self.assertEqual(tax_filing2.account_to_id.id, self.input_vat_acct.id)
        self.assertEqual(tax_filing2.account_adjust_id.id, self.adjust_acct.id)
