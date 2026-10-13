# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from dateutil.rrule import MONTHLY

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_th_account_tax.tests.test_withholding_tax import (
    TestWithholdingTax,
)


@tagged("post_install", "-at_install")
class TestWithholdingTaxReport(TestWithholdingTax):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wht_wizard_obj = cls.env["withholding.tax.report.wizard"]
        cls.date_range_obj = cls.env["date.range"]
        cls.range_type_obj = cls.env["date.range.type"]
        cls.report_obj = cls.env["ir.actions.report"]
        cls.wht_cert_obj = cls.env["withholding.tax.cert"]

        # Create date range
        cls.date_range_type = cls.range_type_obj.create({"name": "TestQuarter"})
        cls.year = datetime.datetime.now().year
        cls._create_date_range_year()
        cls.date_range = cls.date_range_obj.search([], limit=1)
        cls.last_date_range = cls.date_range_obj.search(
            [], limit=1, order="date_start desc"
        )
        cls.report = cls.report_obj._get_report_from_name("withholding.tax.report.xlsx")

        # Create Bank Partner
        cls.bank_partner = cls.env["res.partner.bank"].create(
            {
                "acc_number": "123456789",
                "partner_id": cls.partner_1.id,
            }
        )

        # Create demo for test
        cls.cert_pnd1 = cls._create_withholding_tax("pnd1")
        cls.cert_pnd1.tax_payer = "paid_one_time"
        cls.cert_pnd1.wht_line.write(
            {
                "wht_cert_income_code": cls.env.ref(
                    "l10n_th_account_tax.withholding_tax_pnd1_401n"
                ).id
            }
        )
        cls.cert_pnd3 = cls._create_withholding_tax("pnd3")
        cls.cert_pnd53 = cls._create_withholding_tax("pnd53")
        cls.cert_pnd53.tax_payer = "paid_continue"
        # Create withholding tax wizard
        cls.wht_report_pnd1_wizard = cls.wht_wizard_obj.create(
            {
                "income_tax_form": "pnd1",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )
        cls.wht_report_pnd2_wizard = cls.wht_wizard_obj.create(
            {
                "income_tax_form": "pnd2",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )
        cls.wht_report_pnd3_wizard = cls.wht_wizard_obj.create(
            {
                "income_tax_form": "pnd3",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )
        cls.wht_report_pnd53_wizard = cls.wht_wizard_obj.create(
            {
                "income_tax_form": "pnd53",
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )

    @classmethod
    def _create_date_range_year(self):
        Generator = self.env["date.range.generator"]
        generator = Generator.create(
            {
                "date_start": f"{self.year}-01-01",
                "name_prefix": f"{self.year}/Test/Y-",
                "type_id": self.date_range_type.id,
                "duration_count": 12,
                "unit_of_time": str(MONTHLY),
                "count": 1,
            }
        )
        generator.action_apply()

    @classmethod
    def _create_withholding_tax(self, income_tax_form):
        invoice = self._create_invoice(
            self,
            self.partner_1.id,
            self.purchase_journal.id,
            "in_invoice",
            self.expense_account.id,
            price_unit=100.0,
        )
        invoice.name = "/"
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        invoice.action_post()
        # Payment by writeoff with withholding tax account
        ctx = {
            "active_ids": invoice.line_ids.ids,
            "active_model": "account.move.line",
        }
        register_payment = Form(
            self.env["account.payment.register"].with_context(**ctx),
        ).save()
        action_payment = register_payment.action_create_payments()
        payment = self.env[action_payment["res_model"]].browse(action_payment["res_id"])
        payment.wht_move_ids.write({"wht_cert_income_type": "1"})
        payment.create_wht_cert()
        res = payment.button_wht_certs()
        cert = self.wht_cert_obj.search(res["domain"])
        cert.income_tax_form = income_tax_form
        cert.action_done()
        return cert

    def test_01_wht_button_export_html(self):
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
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )

        # Check file download should name tax + date
        report_name = self.wht_report_pnd3_wizard._get_report_base_filename()
        format_date = self.env["thai.utils"].format_thai_date(
            self.wht_report_pnd3_wizard.date_from,
            month_format="numeric",
            format_date="{year}{month}",
        )
        self.assertEqual(report_name, f"WHT-P03-{format_date}")

    def test_02_wht_button_export_pdf_std(self):
        report = self.wht_report_pnd3_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["wht_report_data"]), 1)
        self.assertFalse(res_data["wht_groupby_partner"])
        self.assertEqual(res_data["wht_report_format"], "std")
        self.assertEqual(report["name"], "Withholding Tax Report")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )

    def test_03_wht_button_export_pdf_rd(self):
        # Check change config standard to rd
        self.env.user.company_id.wht_report_format = "rd"
        report = self.wht_report_pnd3_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["wht_report_data"]), 1)
        self.assertFalse(res_data["wht_groupby_partner"])
        self.assertEqual(res_data["wht_report_format"], "rd")
        self.assertEqual(report["name"], "Withholding Tax Report (RD)")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_rd_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )

        # Allow group by partner by filter PND1A or send context need_group_by_partner=1
        res_data = (
            self.env["report.l10n_th_account_tax_report.report_rd_withholding_tax"]
            .with_context(need_group_by_partner=1)
            ._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        )
        self.assertEqual(len(res_data["wht_groupby_partner"]), 1)

    def test_04_wht_button_export_xlsx(self):
        report = self.wht_report_pnd3_wizard.button_export_xlsx()

        self.assertEqual(report["name"], "Withholding Tax Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax_xlsx/{self.wht_report_pnd3_wizard.id}",
        )

        # Check report XLS action and generate report
        report_model = "report.l10n_th_account_tax_report.report_withholding_tax_xlsx"
        model = self.env[report_model].with_context(
            active_model=self.wht_report_pnd3_wizard._name, **report["context"]
        )
        model.create_xlsx_report(self.wht_report_pnd3_wizard.ids, data=report["data"])

    def test_05_wht_button_export_text_file_pnd3(self):
        report = self.wht_report_pnd3_wizard.button_export_txt()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax_text"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])

        # Check text file value is not empty
        self.assertTrue(res_data["text_file_value"])
        self.assertEqual(report["name"], "Withholding Tax Report Text")
        self.assertEqual(report["report_type"], "qweb-text")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax_text/{self.wht_report_pnd3_wizard.id}",
        )
        tax_payer = res_data["text_file_value"].split("|")[-1].strip()
        self.assertEqual(tax_payer, "1")

    def test_06_wht_button_export_text_file_pnd53(self):
        report = self.wht_report_pnd53_wizard.button_export_txt()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax_text"
        ]._get_report_values(self.wht_report_pnd53_wizard.ids, report["data"])

        # Check text file value is not empty
        self.assertTrue(res_data["text_file_value"])
        self.assertEqual(report["name"], "Withholding Tax Report Text")
        self.assertEqual(report["report_type"], "qweb-text")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax_text/{self.wht_report_pnd53_wizard.id}",
        )
        tax_payer = res_data["text_file_value"].split("|")[-1].strip()
        self.assertEqual(tax_payer, "2")

    def test_07_wht_button_export_text_file_pnd53_multi_line(self):
        # Add multi line to PND53
        self.env["withholding.tax.cert.line"].create(
            {
                "cert_id": self.cert_pnd53.id,
                "wht_cert_income_type": "6",
                "wht_cert_income_desc": "อื่น ๆ",
                "amount": 3.0,
                "base": 100.0,
            }
        )
        # Copy neew PND53 with 1 line
        cert53_copy = self.cert_pnd53.copy({"date": self.cert_pnd53.date})
        self.env["withholding.tax.cert.line"].create(
            {
                "cert_id": cert53_copy.id,
                "wht_cert_income_type": "4A",
                "wht_cert_income_desc": "4. ดอกเบี้ย ฯลฯ 40(4)ก",
                "wht_cert_bank_account": self.bank_partner.id,
                "amount": 3.0,
                "base": 100.0,
            }
        )
        cert53_copy.income_tax_form = "pnd53"
        cert53_copy.action_done()

        report = self.wht_report_pnd53_wizard.button_export_txt()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax_text"
        ]._get_report_values(self.wht_report_pnd53_wizard.ids, report["data"])

        # Check text file value is not empty
        self.assertTrue(res_data["text_file_value"])
        self.assertEqual(report["name"], "Withholding Tax Report Text")
        self.assertEqual(report["report_type"], "qweb-text")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax_text/{self.wht_report_pnd53_wizard.id}",
        )
        # 2 Cert in 1 Text File
        cert_text_data = res_data["text_file_value"].split("\n")
        self.assertEqual(len(cert_text_data), 3)  # 2 Data + 1 Empty

        # 1 Line Text file included 1 Header + multi line (Max 3 lines)
        # and it should equal max lines
        self.assertEqual(len(cert_text_data[0].split("|")), 23)
        self.assertEqual(len(cert_text_data[1].split("|")), 23)

    def test_08_wht_button_export_text_file_pnd1(self):
        report = self.wht_report_pnd1_wizard.button_export_txt()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax_text"
        ]._get_report_values(self.wht_report_pnd1_wizard.ids, report["data"])

        # Check text file value is not empty
        self.assertTrue(res_data["text_file_value"])
        self.assertEqual(report["name"], "Withholding Tax Report Text")
        self.assertEqual(report["report_type"], "qweb-text")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax_text/{self.wht_report_pnd1_wizard.id}",
        )
        text_file_value = res_data["text_file_value"].split("|")
        income_code = text_file_value[0].strip()
        tax_payer = text_file_value[-1].strip()
        self.assertEqual(income_code, "401N")
        self.assertEqual(tax_payer, "3")

    def test_09_wht_button_export_text_file_no_implement(self):
        """Test export text file no implement"""
        report = self.wht_report_pnd2_wizard.button_export_txt()

        with self.assertRaisesRegex(UserError, "Not implement"):
            self.env[
                "report.l10n_th_account_tax_report.report_withholding_tax_text"
            ]._get_report_values(self.wht_report_pnd2_wizard.ids, report["data"])
