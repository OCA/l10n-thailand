# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo.modules.module import get_resource_path
from odoo.tests.common import SavepointCase


class TestWithholdingTaxReport(SavepointCase):
    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(
            cls.cr,
            module,
            get_resource_path(module, *args),
            {},
            "init",
            False,
            "test",
            cls.registry._assertion_report,
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._load("account", "test", "account_minimal_test.xml")
        cls._load("l10n_th_withholding_tax_report", "tests", "date_range_test_data.xml")
        Report = cls.env["ir.actions.report"]
        cls.report_name = "withholding.tax.report.xlsx"
        cls.report = Report._get_report_from_name(cls.report_name)
        cls.model = cls.env["withholding.tax.report"]
        cls.wizard = cls.env["withholding.tax.report.wizard"]

    def _getBaseFilters(self, date_range):
        return {
            "company_id": self.env.user.company_id.id,
            "income_tax_form": "pnd3",
            "date_range_id": date_range.id,
            "date_from": date_range.date_start,
            "date_to": date_range.date_end,
        }

    def test_01_withholding_tax_report(self):
        date_range = self.browse_ref("l10n_th_withholding_tax_report.date_range_test")
        report = self.wizard.create(
            {"income_tax_form": "pnd3", "date_range_id": date_range.id}
        )
        report.button_export_html()
        report.button_export_pdf()
        report.button_export_xlsx()
        report.button_export_txt()

    def test_02_create_text_file(self):
        date_range = self.browse_ref("l10n_th_withholding_tax_report.date_range_test")
        withholding_tax_report = self.model.create(self._getBaseFilters(date_range))
        withholding_tax_report._compute_results()
        text = withholding_tax_report._create_text(withholding_tax_report)
        if text:
            text.split("|")
            self.assertEqual(text[0], "1")

    def test_03_create_xlsx_file(self):
        date_range = self.browse_ref("l10n_th_withholding_tax_report.date_range_test")
        withholding_tax_report = self.model.create(self._getBaseFilters(date_range))
        withholding_tax_report._compute_results()
        report = self.report
        self.assertEqual(report.report_type, "xlsx")
        report.render_xlsx(withholding_tax_report.id, None)
