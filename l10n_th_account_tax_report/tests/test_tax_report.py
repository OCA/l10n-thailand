# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import datetime

from dateutil.rrule import MONTHLY
from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestTaxReport(AccountTestInvoicingCommon):
    @classmethod
    @freeze_time("2001-01-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.date_range_obj = cls.env["date.range"]
        cls.company = cls.env.company
        cls.income_account = cls.company_data["default_account_revenue"]
        cls.tax_report_wizard = cls.env["tax.report.wizard"]
        # Create date range
        cls._create_date_range(cls)
        cls.date_range = cls.date_range_obj.search([], limit=1, order="date_start asc")
        cls.last_date_range = cls.date_range_obj.search(
            [], limit=1, order="date_start desc"
        )
        # Create vendor bills
        cls.bill = cls.init_invoice(
            move_type="in_invoice",
            partner=cls.env.ref("base.res_partner_1"),
            invoice_date=cls.date_range.date_end,
            products=cls.env.ref("product.product_product_7"),
            amounts=[100.0],
            taxes=cls.tax_purchase_a,
        )
        cls.bill.tax_invoice_ids.write(
            {
                "tax_invoice_number": "TEST",
                "tax_invoice_date": cls.date_range.date_end,
            }
        )
        cls.bill.action_post()

        cls.tax_purchase_report_wizard = cls.tax_report_wizard.create(
            {
                "company_id": cls.company.id,
                "tax_id": cls.tax_purchase_a.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )
        # Create customer invoices
        cls.invoice = cls.init_invoice(
            move_type="out_invoice",
            partner=cls.env.ref("base.res_partner_1"),
            invoice_date=cls.date_range.date_end,
            products=cls.env.ref("product.product_product_7"),
            post=True,
            amounts=[100.0],
            taxes=cls.tax_sale_a,
        )

        cls.tax_sale_report_wizard = cls.tax_report_wizard.create(
            {
                "company_id": cls.company.id,
                "tax_id": cls.tax_sale_a.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )

    @freeze_time("2001-01-01")
    def _create_date_range(self):
        RangeType = self.env["date.range.type"]
        Generator = self.env["date.range.generator"]
        range_type = RangeType.create({"name": "Period"})
        year = datetime.datetime.now().year
        generator = Generator.create(
            {
                "name_prefix": f"{year}-",
                "duration_count": 1,
                "unit_of_time": str(MONTHLY),
                "count": 12,
                "type_id": range_type.id,
                "date_start": f"{year}-01-01",
            }
        )
        generator.action_apply()

    def test_01_button_export_html(self):
        report = self.tax_purchase_report_wizard.button_export_html()
        self.assertEqual(report["name"], "Thai TAX Report")
        self.assertEqual(report["report_type"], "qweb-html")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_thai_tax/{self.tax_purchase_report_wizard.id}",
        )

    def test_02_button_export_pdf_std(self):
        # Check data query, it should have data
        self.tax_purchase_report_wizard.show_cancel = False
        report = self.tax_purchase_report_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_thai_tax"
        ]._get_report_values(self.tax_purchase_report_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["tax_report_data"]), 1)
        self.assertEqual(res_data["tax_report_format"], "std")
        self.assertEqual(report["name"], "Thai TAX Report")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_thai_tax/{self.tax_purchase_report_wizard.id}",
        )

    def test_03_button_export_pdf_rd(self):
        # Check change config standard to rd
        self.env.user.company_id.tax_report_format = "rd"
        report = self.tax_purchase_report_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_thai_tax"
        ]._get_report_values(self.tax_purchase_report_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["tax_report_data"]), 1)
        self.assertEqual(res_data["tax_report_format"], "rd")
        self.assertEqual(report["name"], "Thai TAX Report (RD)")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_rd_thai_tax/{self.tax_purchase_report_wizard.id}",
        )

        # Check file download should name tax + date
        report_name = self.tax_purchase_report_wizard._get_report_base_filename()
        format_date = self.tax_purchase_report_wizard.format_thai_date(
            self.tax_purchase_report_wizard.date_from,
            month_format="numeric",
            format_date="{year}{month}",
        )
        self.assertEqual(
            report_name,
            f"{self.tax_purchase_report_wizard.tax_id.display_name}-{format_date}",
        )
        # Display Header
        dict_format = self.tax_purchase_report_wizard._get_period_be(
            self.date_range.date_start, self.date_range.date_end
        )
        self.assertEqual(dict_format, ["มกราคม", "2544"])

    def test_04_button_export_xlsx_purchase_vat(self):
        # Test onchange date range
        self.assertEqual(
            self.tax_purchase_report_wizard.date_from, self.date_range.date_start
        )
        self.assertEqual(
            self.tax_purchase_report_wizard.date_to, self.date_range.date_end
        )
        with Form(self.tax_purchase_report_wizard) as f:
            f.date_range_id = self.last_date_range
        f.save()
        self.assertEqual(
            self.tax_purchase_report_wizard.date_from, self.last_date_range.date_start
        )
        self.assertEqual(
            self.tax_purchase_report_wizard.date_to, self.last_date_range.date_end
        )
        # Change back to first date range
        with Form(self.tax_purchase_report_wizard) as f:
            f.date_range_id = self.date_range

        # Check date from > date to, it should error
        with self.assertRaises(UserError):
            with Form(self.tax_purchase_report_wizard) as f:
                f.date_from = "2020-01-05"
                f.date_to = "2020-01-01"

        # generate xlsx (Purchase Vat)
        report = self.tax_purchase_report_wizard.button_export_xlsx()

        self.assertEqual(report["name"], "Thai TAX Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_thai_tax_xlsx/{self.tax_purchase_report_wizard.id}",
        )

        # Check report XLS action and generate report
        report_model = "report.l10n_th_account_tax_report.report_thai_tax_xlsx"
        model = self.env[report_model].with_context(
            active_model=self.tax_purchase_report_wizard._name,
            **report["context"],
        )
        model.create_xlsx_report(
            self.tax_purchase_report_wizard.ids, data=report["data"]
        )

    def test_05_button_export_xlsx_sale_vat(self):
        # generate xlsx (Sale Vat)
        report = self.tax_sale_report_wizard.button_export_xlsx()

        self.assertEqual(report["name"], "Thai TAX Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_thai_tax_xlsx/{self.tax_sale_report_wizard.id}",
        )

        # Check report XLS action and generate report
        report_model = "report.l10n_th_account_tax_report.report_thai_tax_xlsx"
        model = self.env[report_model].with_context(
            active_model=self.tax_purchase_report_wizard._name,
            **report["context"],
        )
        model.create_xlsx_report(
            self.tax_purchase_report_wizard.ids, data=report["data"]
        )
