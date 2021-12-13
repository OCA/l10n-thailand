# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import datetime

from dateutil.rrule import MONTHLY

from odoo.tests.common import SavepointCase


class TestTaxReport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_obj = cls.env["tax.report.wizard"]
        cls.date_range_obj = cls.env["date.range"]
        cls.tax_report_obj = cls.env["report.tax.report"]
        cls._create_date_range(cls)
        cls.company = cls.env.company
        cls.tax = cls.env.ref("l10n_generic_coa.1_sale_tax_template")
        cls.taxp = cls.env.ref("l10n_generic_coa.1_purchase_tax_template")
        cls.date_range = cls.date_range_obj.search([], limit=1, order="date_start asc")

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

    def test_01_button_export_html(self):
        wizard = self.wizard_obj.create(
            {
                "company_id": self.company.id,
                "tax_id": self.tax.id,
                "date_range_id": self.date_range.id,
            }
        )
        report = wizard.button_export_html()
        self.assertEqual(report["name"], "TAX Report")
        self.assertEqual(report["type"], "ir.actions.client")
        self.assertEqual(report["tag"], "l10n_th_account_tax_report_backend")
        self.assertEqual(report["context"]["active_model"], "report.tax.report")

    def test_02_button_export_pdf(self):
        wizard = self.wizard_obj.create(
            {
                "company_id": self.company.id,
                "tax_id": self.tax.id,
                "date_range_id": self.date_range.id,
            }
        )
        report = wizard.button_export_pdf()
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

    def test_03_button_export_xlsx(self):
        wizard = self.wizard_obj.create(
            {
                "company_id": self.company.id,
                "tax_id": self.tax.id,
                "date_range_id": self.date_range.id,
            }
        )
        report = wizard.button_export_xlsx()
        self.assertEqual(report["name"], "TAX Report XLSX")
        self.assertEqual(report["type"], "ir.actions.report")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"], "l10n_th_account_tax_report.report_tax_report_xlsx"
        )
        self.assertEqual(report["report_file"], "Tax Report")
        tax_report = self.tax_report_obj.browse(report["context"]["active_ids"])
        tax_report._compute_results()
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

    def test_04_button_export_xlsx_purchase(self):
        wizard = self.wizard_obj.create(
            {
                "company_id": self.company.id,
                "tax_id": self.taxp.id,
                "date_range_id": self.date_range.id,
            }
        )
        report = wizard.button_export_xlsx()
        self.assertEqual(report["name"], "TAX Report XLSX")
        self.assertEqual(report["type"], "ir.actions.report")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"], "l10n_th_account_tax_report.report_tax_report_xlsx"
        )
        self.assertEqual(report["report_file"], "Tax Report")
        tax_report = self.tax_report_obj.browse(report["context"]["active_ids"])
        tax_report._compute_results()
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
