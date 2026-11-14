# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from unittest.mock import patch

from dateutil.rrule import MONTHLY
from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools import SQL

from odoo.addons.l10n_th_account_tax.tests.common import ThAccountTaxCommon


@tagged("post_install", "-at_install")
@freeze_time("2001-01-01")
class TestTaxReport(ThAccountTaxCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_range_obj = cls.env["date.range"]
        cls.tax_report_wizard = cls.env["tax.report.wizard"]
        # Create date range
        cls._create_date_range()
        cls.date_range = cls.date_range_obj.search(
            [("type_id", "=", cls.range_type.id)], limit=1, order="date_start asc"
        )
        cls.last_date_range = cls.date_range_obj.search(
            [("type_id", "=", cls.range_type.id)], limit=1, order="date_start desc"
        )
        # Create vendor bills
        cls.bill = cls._create_th_invoice(
            "in_invoice",
            [(100.0, cls.input_vat)],
            partner=cls.partner_b,
            date=cls.date_range.date_end,
        )
        cls._fill_tax_invoice(cls.bill, number="TEST", date=cls.date_range.date_end)
        cls.bill.action_post()

        cls.tax_purchase_report_wizard = cls.tax_report_wizard.create(
            {
                "company_id": cls.company.id,
                "tax_id": cls.input_vat.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )
        # Create customer invoices
        cls.invoice = cls._create_th_invoice(
            "out_invoice",
            [(100.0, cls.output_vat)],
            partner=cls.partner_a,
            date=cls.date_range.date_end,
            post=True,
        )

        cls.tax_sale_report_wizard = cls.tax_report_wizard.create(
            {
                "company_id": cls.company.id,
                "tax_id": cls.output_vat.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )

    @classmethod
    def _create_date_range(cls):
        cls.range_type = cls.env["date.range.type"].create({"name": "Period"})
        generator = cls.env["date.range.generator"].create(
            {
                "name_prefix": "2001-",
                "duration_count": 1,
                "unit_of_time": str(MONTHLY),
                "count": 12,
                "type_id": cls.range_type.id,
                "date_start": "2001-01-01",
            }
        )
        generator.action_apply()

    def _get_purchase_report_lines(self):
        report = self.env["report.l10n_th_account_tax_report.report_thai_tax"]
        res_data = report._get_report_values(self.tax_purchase_report_wizard.ids, {})
        return res_data["tax_report_data"]

    def _render_html(self, wizard):
        report_name, data = wizard._get_report_name("qweb-html")
        return self.env["ir.actions.report"]._render_qweb_html(
            report_name, wizard.ids, data=data
        )[0]

    def test_01_button_export_html(self):
        wht_tax = self._create_wht_tax("WHT 3%")
        selectable_taxes = self.env["account.tax"].search(
            self.tax_report_wizard._fields["tax_id"].domain
        )
        self.assertIn(self.input_vat, selectable_taxes)
        self.assertNotIn(wht_tax, selectable_taxes)

        report = self.tax_purchase_report_wizard.button_export_html()
        self.assertEqual(report["name"], "Thai TAX Report")
        self.assertEqual(report["report_type"], "qweb-html")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_thai_tax/{self.tax_purchase_report_wizard.id}",
        )
        html = self._render_html(self.tax_purchase_report_wizard)
        self.assertIn(b"TEST", html)
        self.assertIn(b'res-model="account.move"', html)
        self.assertIn(f'res-id="{self.bill.id}"'.encode(), html)
        self.assertIn(b'res-model="res.partner"', html)

    def test_02_button_export_pdf_std(self):
        # Check data query, it should have data
        self.tax_purchase_report_wizard.show_cancel = False
        report = self.tax_purchase_report_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_thai_tax"
        ]._get_report_values(self.tax_purchase_report_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["tax_report_data"]), 1)
        self.assertEqual(res_data["total_base"], 100.0)
        self.assertEqual(res_data["total_tax"], 7.0)
        # Head office of a juristic person
        self.assertEqual(res_data["tax_report_data"][0]["partner_branch"], "00000")
        self.assertEqual(res_data["tax_report_format"], "std")
        self.assertEqual(report["name"], "Thai TAX Report")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_thai_tax/{self.tax_purchase_report_wizard.id}",
        )

    def test_03_button_export_pdf_rd(self):
        # Check change config standard to rd
        self.company.tax_report_format = "rd"
        report = self.tax_purchase_report_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_thai_tax"
        ]._get_report_values(self.tax_purchase_report_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["tax_report_data"]), 1)
        self.assertEqual(res_data["tax_report_format"], "rd")
        self.assertEqual(len(res_data["rd_pages"]), 1)
        # A long name wraps: the pages are split by the height of the rows
        report_rd = self.env["report.l10n_th_account_tax_report.report_rd_thai_tax"]
        line = dict(res_data["tax_report_data"][0])
        self.assertEqual(report_rd._get_rd_line_count(line), 1)
        line["partner_name"] = "บริษัท ไทยพัฒนาอุตสาหกรรมการเกษตรและอาหารแปรรูป " * 3
        self.assertGreater(report_rd._get_rd_line_count(line), 1)
        self.assertGreater(len(report_rd._get_rd_pages([line] * 15)), 1)
        self.assertEqual(
            res_data["company_address"],
            self.company.partner_id._display_address(without_name=True),
        )
        html = self._render_html(self.tax_purchase_report_wizard)
        self.assertIn(b"TEST", html)
        self.assertIn(b'res-model="account.move"', html)
        self.assertIn(f'res-id="{self.bill.id}"'.encode(), html)
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
        with self.assertRaises(UserError), Form(self.tax_purchase_report_wizard) as f:
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
        content, file_type = model.create_xlsx_report(
            self.tax_purchase_report_wizard.ids, data=report["data"]
        )
        self.assertEqual(file_type, "xlsx")
        self.assertTrue(content)

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
            active_model=self.tax_sale_report_wizard._name,
            **report["context"],
        )
        content, file_type = model.create_xlsx_report(
            self.tax_sale_report_wizard.ids, data=report["data"]
        )
        self.assertEqual(file_type, "xlsx")
        self.assertTrue(content)

    def test_06_merge_same_tax_invoice_number(self):
        """Two bills sharing one vendor tax invoice number collapse to a single
        report line with summed base and tax. This is the group-payment case
        where one vendor tax invoice covers multiple bills."""
        bill1 = self.bill

        bill2 = self._create_th_invoice(
            "in_invoice",
            [(100.0, self.input_vat)],
            partner=self.partner_b,
            date=self.date_range.date_end,
        )
        self._fill_tax_invoice(bill2, number="TEST", date=self.date_range.date_end)
        bill2.action_post()

        lines = [
            line
            for line in self._get_purchase_report_lines()
            if line["tax_invoice_number"] == "TEST"
        ]
        self.assertEqual(len(lines), 1)
        tax_invoices = (bill1 + bill2).tax_invoice_ids
        self.assertEqual(
            lines[0]["tax_base_amount"],
            sum(tax_invoices.mapped("tax_base_amount")),
        )
        self.assertEqual(lines[0]["tax_amount"], sum(tax_invoices.mapped("balance")))
        self.assertEqual(
            {target_id for label, target_id in lines[0]["doc_refs"]},
            {bill1.id, bill2.id},
        )

    def test_07_distinct_tax_invoice_numbers_not_merged(self):
        """Different vendor tax invoice numbers stay as separate report lines."""
        bill2 = self._create_th_invoice(
            "in_invoice",
            [(100.0, self.input_vat)],
            partner=self.partner_b,
            date=self.date_range.date_end,
        )
        self._fill_tax_invoice(bill2, number="TEST222", date=self.date_range.date_end)
        bill2.action_post()
        numbers = [
            line["tax_invoice_number"] for line in self._get_purchase_report_lines()
        ]
        self.assertEqual(len([n for n in numbers if n in ("TEST", "TEST222")]), 2)

    def test_08_undue_vat_links_origin_invoice(self):
        """Undue VAT lines come from the cash basis entry, the link opens the
        invoice"""
        undue_vat = self._create_vat_tax(
            "Undue Output VAT 7%",
            "sale",
            7.0,
            self._create_account("Output VAT Paid", "O7P", "liability_current"),
            exigibility="on_payment",
            transition_account=self._create_account(
                "Undue Output VAT", "UNDUE7", "liability_current"
            ),
        )
        invoice = self._create_th_invoice(
            "out_invoice",
            [(100.0, undue_vat)],
            partner=self.partner_a,
            date=self.date_range.date_end,
            post=True,
        )
        self._pay(invoice, inbound=True)
        wizard = self.tax_report_wizard.create(
            {
                "company_id": self.company.id,
                "tax_id": undue_vat.id,
                "date_from": self.date_range.date_start,
                "date_to": self.date_range.date_end,
            }
        )
        report = self.env["report.l10n_th_account_tax_report.report_thai_tax"]
        lines = report._get_report_values(wizard.ids, {})["tax_report_data"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["doc_refs"], [(invoice.name, invoice.id)])

    def test_09_query_hooks(self):
        """Other modules extend the query with SQL parts, e.g. a condition with
        a parameter"""
        report = self.env["report.l10n_th_account_tax_report.report_thai_tax"]
        data = self.tax_purchase_report_wizard._prepare_report_tax()
        self.assertEqual(len(report._get_tax_data(data)), 1)
        where = report._query_where_tax(data)
        with patch.object(
            type(report),
            "_query_where_tax",
            lambda rep, data: SQL(
                "%s AND t.partner_id != %s", where, self.partner_b.id
            ),
        ):
            self.assertFalse(report._get_tax_data(data))
