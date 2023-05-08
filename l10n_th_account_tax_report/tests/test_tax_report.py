# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import datetime

from dateutil.rrule import MONTHLY
from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestTaxReport(TransactionCase):
    @classmethod
    @freeze_time("2001-01-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.date_range_obj = cls.env["date.range"]
        cls.tax_report_obj = cls.env["report.tax.report"]
        cls.company = cls.env.company
        cls.tax = cls.env.ref("l10n_generic_coa.1_sale_tax_template")
        cls.taxp = cls.env.ref("l10n_generic_coa.1_purchase_tax_template")
        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.product1 = cls.env.ref("product.product_product_7")
        # Create date range
        cls._create_date_range(cls)
        cls.date_range = cls.date_range_obj.search([], limit=1, order="date_start asc")
        cls.last_date_range = cls.date_range_obj.search(
            [], limit=1, order="date_start desc"
        )
        # Create vendor Bills
        cls._create_bills(cls, "in_invoice")
        cls.tax_purchase_report_wizard = cls.env["tax.report.wizard"].create(
            {
                "company_id": cls.company.id,
                "tax_id": cls.taxp.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
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

    def _create_bills(self, move_type):
        taxes = self.taxp if move_type == "in_invoice" else self.tax
        date = self.date_range.date_end
        moves = self.env["account.move"].create(
            {
                "partner_id": self.partner1,
                "move_type": move_type,
                "invoice_date": date,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [taxes.id])],
                        },
                    )
                ],
            }
        )
        # add tax invoice
        moves.tax_invoice_ids.write(
            {"tax_invoice_number": "TEST", "tax_invoice_date": date}
        )
        moves.action_post()

    def test_01_button_export_html(self):
        report = self.tax_purchase_report_wizard.button_export_html()
        self.assertEqual(report["name"], "TAX Report")
        self.assertEqual(report["type"], "ir.actions.client")
        self.assertEqual(report["tag"], "l10n_th_account_tax_report_backend")
        self.assertEqual(report["context"]["active_model"], "report.tax.report")

        # Check send report type is not supported, it should error
        with self.assertRaises(UserError):
            self.tax_purchase_report_wizard._export("qweb-text")

    def test_02_button_export_pdf(self):
        report = self.tax_purchase_report_wizard.button_export_pdf()
        self.assertEqual(report["name"], "TAX Report PDF")
        self.assertEqual(report["type"], "ir.actions.report")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            "l10n_th_account_tax_report.report_tax_report_pdf",
        )
        self.assertEqual(
            report["report_file"], "l10n_th_account_tax_report.report_tax_report_pdf"
        )

        # Check change config standard to rd
        self.env.user.company_id.tax_report_format = "rd"
        report = self.tax_purchase_report_wizard.button_export_pdf()
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_file"], "l10n_th_account_tax_report.report_rd_tax_report_pdf"
        )

    def test_03_button_export_xlsx_purchase(self):
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

        # generate xlsx
        report = self.tax_purchase_report_wizard.button_export_xlsx()
        self.assertEqual(report["name"], "TAX Report XLSX")
        self.assertEqual(report["type"], "ir.actions.report")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"], "l10n_th_account_tax_report.report_tax_report_xlsx"
        )
        self.assertEqual(report["report_file"], "Tax Report")
        tax_report = self.tax_report_obj.browse(report["context"]["active_ids"])
        tax_report._compute_results()
        # Test render html
        res = tax_report.get_html(
            given_context={"active_id": tax_report.id, "model": "report.tax.report"}
        )
        self.assertTrue(res["html"])
        action = self.env.ref("l10n_th_account_tax_report.action_tax_report_xlsx")
        action._render_xlsx(
            report["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    report["report_name"], str(report["context"]["active_ids"][0])
                ),
                "token": "dummy-because-api-expects-one",
            },
        )

    def test_04_check_function_convert(self):
        """This function test for other with compute in form"""
        res = self.tax_report_obj._get_period_be(
            datetime.date(2020, 1, 1), datetime.date(2020, 1, 31)
        )
        self.assertEqual(res[0], "มกราคม")
        self.assertEqual(res[1], "2563")  # Thai year
