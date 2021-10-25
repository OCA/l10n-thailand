# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from dateutil.rrule import MONTHLY

from odoo.tests.common import SavepointCase


class TestWithholdingTaxReport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_object = cls.env["withholding.tax.report.wizard"]
        cls.date_range_object = cls.env["date.range"]
        cls.range_type_object = cls.env["date.range.type"]
        cls.wht_report_object = cls.env["withholding.tax.report"]
        cls.report_object = cls.env["ir.actions.report"]
        cls.date_range_type = cls.range_type_object.create({"name": "TestQuarter"})
        cls.year = datetime.datetime.now().year
        cls._create_date_range_year(cls)
        cls.date_range = cls.date_range_object.search([], limit=1)
        cls.report = cls.report_object._get_report_from_name(
            "withholding.tax.report.xlsx"
        )

    def _create_date_range_year(self):
        Generator = self.env["date.range.generator"]
        generator = Generator.create(
            {
                "date_start": "%s-01-01" % self.year,
                "name_prefix": "%s/Test/Y-" % self.year,
                "type_id": self.date_range_type.id,
                "duration_count": 12,
                "unit_of_time": str(MONTHLY),
                "count": 1,
            }
        )
        generator.action_apply()

    def _getBaseFilters(self, date_range):
        return {
            "company_id": self.env.user.company_id.id,
            "income_tax_form": "pnd3",
            "date_range_id": date_range.id,
            "date_from": date_range.date_start,
            "date_to": date_range.date_end,
        }

    def test_01_withholding_tax_report(self):
        report = self.wizard_object.create(
            {"income_tax_form": "pnd3", "date_range_id": self.date_range.id}
        )
        report.button_export_html()
        report.button_export_pdf()
        report.button_export_xlsx()
        report.button_export_txt()

    def test_02_create_text_file(self):
        withholding_tax_report = self.wht_report_object.create(
            self._getBaseFilters(self.date_range)
        )
        withholding_tax_report._compute_results()
        report_name = withholding_tax_report._get_report_base_filename()
        self.assertEqual(report_name, "WHT-P03-%s01" % (self.year + 543))
        text = withholding_tax_report._create_text(withholding_tax_report)
        if text:
            text.split("|")
            self.assertEqual(text[0], "1")

    def test_03_create_xlsx_file(self):
        withholding_tax_report = self.wht_report_object.create(
            self._getBaseFilters(self.date_range)
        )
        withholding_tax_report._compute_results()
        self.assertEqual(self.report.report_type, "xlsx")
        self.report._render_xlsx(withholding_tax_report.id, None)
