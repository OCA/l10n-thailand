# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from dateutil.rrule import MONTHLY

from odoo.exceptions import UserError
from odoo.tests.common import Form, tagged

from odoo.addons.l10n_th_account_tax.tests.test_withholding_tax import (
    TestWithholdingTax,
)


@tagged("post_install", "-at_install")
class TestWithholdingTaxReport(TestWithholdingTax):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wht_wizard_object = cls.env["withholding.tax.report.wizard"]
        cls.date_range_object = cls.env["date.range"]
        cls.range_type_object = cls.env["date.range.type"]
        cls.wht_report_object = cls.env["withholding.tax.report"]
        cls.report_object = cls.env["ir.actions.report"]
        cls.date_range_type = cls.range_type_object.create({"name": "TestQuarter"})
        cls.year = datetime.datetime.now().year
        cls._create_date_range_year(cls)
        cls.date_range = cls.date_range_object.search([], limit=1)
        cls.last_date_range = cls.date_range_object.search(
            [], limit=1, order="date_start desc"
        )
        cls.report = cls.report_object._get_report_from_name(
            "withholding.tax.report.xlsx"
        )
        # Create demo for test
        cls.cert_pnd1 = cls._create_withholding_tax(cls, "pnd1")
        cls.cert_pnd3 = cls._create_withholding_tax(cls, "pnd3")
        cls.cert_pnd53 = cls._create_withholding_tax(cls, "pnd53")

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

    def _create_withholding_tax(self, income_tax_form):
        invoice = self._create_invoice(
            self,
            self.partner_1.id,
            self.expenses_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit=100.0,
        )
        invoice.name = "/"
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": [invoice.id],
            "active_id": invoice.id,
            "active_model": "account.move",
        }
        with Form(
            self.account_payment_register.with_context(**ctx),
            view=self.register_view_id,
        ) as f:
            register_payment = f.save()
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        payment.wht_move_ids.write({"wht_cert_income_type": "1"})
        payment.create_wht_cert()
        res = payment.button_wht_certs()
        cert = self.wht_cert.search(res["domain"])
        cert.income_tax_form = income_tax_form
        cert.action_done()
        return cert

    def _getBaseFilters(self, date_range, income_tax_form):
        return {
            "company_id": self.env.user.company_id.id,
            "income_tax_form": income_tax_form,
            "date_range_id": date_range.id,
            "date_from": date_range.date_start,
            "date_to": date_range.date_end,
        }

    def test_01_withholding_tax_report_wizard(self):
        wht_report_wizard = self.wht_wizard_object.create(
            {
                "income_tax_form": "pnd3",
                "date_from": self.date_range.date_start,
                "date_to": self.date_range.date_end,
            }
        )
        # Test onchange date range
        self.assertEqual(wht_report_wizard.date_from, self.date_range.date_start)
        self.assertEqual(wht_report_wizard.date_to, self.date_range.date_end)
        with Form(wht_report_wizard) as f:
            f.date_range_id = self.last_date_range
        f.save()
        self.assertEqual(wht_report_wizard.date_from, self.last_date_range.date_start)
        self.assertEqual(wht_report_wizard.date_to, self.last_date_range.date_end)
        # Check date from > date to, it should error
        with self.assertRaises(UserError):
            with Form(wht_report_wizard) as f:
                f.date_from = "2020-01-05"
                f.date_to = "2020-01-01"

        wht_report_wizard.button_export_html()
        wht_report_wizard.button_export_xlsx()
        wht_report_wizard.button_export_txt()

        # Check export with pdf (pdf with standard)
        action = wht_report_wizard.button_export_pdf()
        self.assertEqual(action["report_type"], "qweb-pdf")
        self.assertEqual(
            action["report_file"],
            "l10n_th_account_tax_report.report_withholding_tax_qweb",
        )

        # Check change config standard to rd
        self.env.user.company_id.wht_report_format = "rd"
        action = wht_report_wizard.button_export_pdf()
        self.assertEqual(action["report_type"], "qweb-pdf")
        self.assertEqual(
            action["report_file"],
            "l10n_th_account_tax_report.report_rd_withholding_tax_qweb",
        )

        # Check function _convert_result_to_dict(), it should convert object to dict
        wht_cert_line = self.env["withholding.tax.cert.line"].search([])
        result_dict = self.wht_report_object._convert_result_to_dict(wht_cert_line)
        self.assertTrue(result_dict[wht_cert_line[0].id])
        self.assertEqual(type(result_dict), type({}))

    def test_02_create_text_file(self):
        # pnd1
        withholding_tax_1_report = self.wht_report_object.create(
            self._getBaseFilters(self.date_range, "pnd1")
        )
        withholding_tax_1_report._compute_results()
        report_name = withholding_tax_1_report._get_report_base_filename()
        self.assertEqual(report_name, "WHT-P01-%s01" % (self.year + 543))
        # Test render html
        res = withholding_tax_1_report.get_html(
            given_context={
                "active_id": withholding_tax_1_report.id,
                "model": "withholding.tax.report",
            }
        )
        self.assertTrue(res["html"])

        text = withholding_tax_1_report._create_text(withholding_tax_1_report)
        if text:
            text.split("|")
            self.assertEqual(text[0], "1")
        # pnd3
        withholding_tax_3_report = self.wht_report_object.create(
            self._getBaseFilters(self.date_range, "pnd3")
        )
        withholding_tax_3_report._compute_results()
        report_name = withholding_tax_3_report._get_report_base_filename()
        self.assertEqual(report_name, "WHT-P03-%s01" % (self.year + 543))
        text = withholding_tax_3_report._create_text(withholding_tax_3_report)
        if text:
            text.split("|")
            self.assertEqual(text[0], "1")
        # pnd53
        withholding_tax_53_report = self.wht_report_object.create(
            self._getBaseFilters(self.date_range, "pnd53")
        )
        withholding_tax_53_report._compute_results()
        report_name = withholding_tax_53_report._get_report_base_filename()
        self.assertEqual(report_name, "WHT-P53-%s01" % (self.year + 543))
        text = withholding_tax_53_report._create_text(withholding_tax_53_report)
        if text:
            text.split("|")
            self.assertEqual(text[0], "1")

    def test_03_create_xlsx_file(self):
        withholding_tax_report = self.wht_report_object.create(
            self._getBaseFilters(self.date_range, "pnd3")
        )
        withholding_tax_report._compute_results()
        self.assertEqual(self.report.report_type, "xlsx")
        self.report._render_xlsx(withholding_tax_report.id, None)
