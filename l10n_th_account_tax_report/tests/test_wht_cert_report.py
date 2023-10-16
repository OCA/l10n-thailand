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
        cls.report_object = cls.env["ir.actions.report"]
        # Create date range
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
        cls.cert_pnd1.tax_payer = "paid_one_time"
        cls.cert_pnd3 = cls._create_withholding_tax(cls, "pnd3")
        cls.cert_pnd53 = cls._create_withholding_tax(cls, "pnd53")
        cls.cert_pnd53.tax_payer = "paid_continue"
        # Create withholding tax wizard
        cls.wht_report_pnd1_wizard = cls.wht_wizard_object.create(
            {
                "income_tax_form": "pnd1",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )
        cls.wht_report_pnd3_wizard = cls.wht_wizard_object.create(
            {
                "income_tax_form": "pnd3",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )
        cls.wht_report_pnd53_wizard = cls.wht_wizard_object.create(
            {
                "income_tax_form": "pnd53",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
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

    def test_01_wht_button_export_html(self):
        # Check data query, it should have data
        self.assertTrue(self.wht_report_pnd3_wizard.results)
        # Test onchange date range
        self.assertEqual(
            self.wht_report_pnd3_wizard.date_from, self.date_range.date_start
        )
        self.assertEqual(self.wht_report_pnd3_wizard.date_to, self.date_range.date_end)
        with Form(self.wht_report_pnd3_wizard) as f:
            f.date_range_id = self.last_date_range
        f.save()
        self.assertEqual(
            self.wht_report_pnd3_wizard.date_from, self.last_date_range.date_start
        )
        self.assertEqual(
            self.wht_report_pnd3_wizard.date_to, self.last_date_range.date_end
        )
        # Check date from > date to, it should error
        with self.assertRaises(UserError):
            with Form(self.wht_report_pnd3_wizard) as f:
                f.date_from = "2020-01-05"
                f.date_to = "2020-01-01"

        report = self.wht_report_pnd3_wizard.button_export_html()
        self.assertEqual(report["name"], "Withholding Tax Report")
        self.assertEqual(report["report_type"], "qweb-html")
        self.assertEqual(
            report["report_name"], "l10n_th_account_tax_report.report_withholding_tax"
        )

        # Check function _convert_result_to_dict(), it should convert object to dict
        wht_cert_line = self.env["withholding.tax.cert.line"].search([])
        result_dict = self.wht_report_pnd3_wizard._convert_result_to_dict(wht_cert_line)
        self.assertTrue(result_dict[wht_cert_line[0].id])
        self.assertEqual(type(result_dict), type({}))

        # Test with pnd1
        wht_cert_line_pnd1 = wht_cert_line.filtered(
            lambda l: l.cert_id.tax_payer == "paid_one_time"
            and l.cert_id.income_tax_form == "pnd1"
        )
        result_dict = self.wht_report_pnd1_wizard._convert_result_to_dict(wht_cert_line)
        self.assertEqual(result_dict[wht_cert_line_pnd1[0].id]["tax_payer"], 3)

        # Test with pnd53
        wht_cert_line_pnd53 = wht_cert_line.filtered(
            lambda l: l.cert_id.tax_payer == "paid_continue"
            and l.cert_id.income_tax_form == "pnd53"
        )
        result_dict = self.wht_report_pnd53_wizard._convert_result_to_dict(
            wht_cert_line
        )
        self.assertEqual(result_dict[wht_cert_line_pnd53[0].id]["tax_payer"], 3)

        # Check file download should name tax + date
        report_name = self.wht_report_pnd3_wizard._get_report_base_filename()
        format_date = self.wht_report_pnd3_wizard.format_date_ym_wht()
        self.assertEqual(report_name, "WHT-P03-{}".format(format_date))

    def test_02_wht_button_export_pdf(self):
        report = self.wht_report_pnd3_wizard.button_export_pdf()
        self.assertEqual(report["name"], "Withholding Tax Report")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"], "l10n_th_account_tax_report.report_withholding_tax"
        )

        # Check change config standard to rd
        self.env.user.company_id.wht_report_format = "rd"
        report = self.wht_report_pnd3_wizard.button_export_pdf()
        self.assertEqual(report["name"], "Withholding Tax Report (RD)")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            "l10n_th_account_tax_report.report_rd_withholding_tax",
        )

        # Test print on html with withholding tax RD, it should change to RD
        wht_report = self.env.ref(
            "l10n_th_account_tax_report.action_print_report_wht_qweb"
        )
        pdf, ttype = wht_report._render_qweb_pdf(wht_report.report_name)
        self.assertEqual(ttype, "html")

    def test_03_wht_button_export_xlsx(self):
        report = self.wht_report_pnd3_wizard.button_export_xlsx()
        self.assertEqual(report["name"], "Withholding Tax Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"],
            "l10n_th_account_tax_report.report_withholding_tax_xlsx",
        )

        # Test export excel by code
        action = self.env.ref("l10n_th_account_tax_report.action_print_report_wht_xlsx")
        report_xlsx = action._render_xlsx(
            action.report_name,
            report["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    report["report_name"], str(report["context"]["active_ids"][0])
                ),
                "token": "dummy-because-api-expects-one",
            },
        )
        self.assertEqual(report_xlsx[1], "xlsx")

    def test_04_wht_button_export_text_file(self):
        report = self.wht_report_pnd3_wizard.button_export_txt()
        self.assertEqual(report["name"], "Withholding Tax Report Text")
        self.assertEqual(report["report_type"], "qweb-text")
        self.assertEqual(
            report["report_name"],
            "l10n_th_account_tax_report.report_withholding_tax_text",
        )

        # test render text file pnd1 with code
        text_pnd1 = self.wht_report_pnd1_wizard._create_text(
            self.wht_report_pnd1_wizard
        )
        self.assertEqual(text_pnd1[0], "1")

        # test render text file pnd3 with code
        text_pnd3 = self.wht_report_pnd3_wizard._create_text(
            self.wht_report_pnd3_wizard
        )
        self.assertEqual(text_pnd3[0], "1")
        # pnd1 no address data to output
        self.assertTrue(len(text_pnd1) < len(text_pnd3))

        # test render text file pnd53 with code
        text_pnd53 = self.wht_report_pnd53_wizard._create_text(
            self.wht_report_pnd53_wizard
        )
        self.assertEqual(text_pnd53[0], "1")
        # pnd1 no address data to output
        self.assertTrue(len(text_pnd1) < len(text_pnd53))
