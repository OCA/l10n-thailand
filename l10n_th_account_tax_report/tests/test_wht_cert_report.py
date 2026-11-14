# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.rrule import MONTHLY
from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_th_account_tax.tests.common import ThAccountTaxCommon


@tagged("post_install", "-at_install")
@freeze_time("2026-01-15")
class TestWithholdingTaxReport(ThAccountTaxCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wht_wizard_obj = cls.env["withholding.tax.report.wizard"]
        cls.wht_cert_obj = cls.env["withholding.tax.cert"]
        cls.wht_tax = cls._create_wht_tax("WHT Purchase Service 3%", amount=-3.0)
        # Tax ID of an individual (partner_a) and a juristic person (partner_b)
        cls.partner_a.vat = "1101700123456"
        cls.partner_b.vat = "0105555123450"
        cls.partner_a.l10n_th_title = "mr"
        cls.partner_b.additional_identifiers = {"TH_BRANCH_CODE": "00001"}

        # Create date range
        cls.date_range_type = cls.env["date.range.type"].create({"name": "TestMonth"})
        cls._create_date_ranges()
        date_ranges = cls.env["date.range"].search(
            [("type_id", "=", cls.date_range_type.id)], order="date_start"
        )
        cls.date_range = date_ranges[0]
        cls.last_date_range = date_ranges[-1]

        # Create Bank Partner
        cls.bank_partner = cls.env["res.partner.bank"].create(
            {
                "account_number": "123456789",
                "partner_id": cls.partner_b.id,
            }
        )

        # Create demo for test
        cls.cert_pnd1 = cls._create_withholding_tax(
            "pnd1",
            tax_payer="paid_one_time",
            line_vals={
                "wht_cert_income_type": "1",
                "wht_cert_income_code": cls.env.ref(
                    "l10n_th_account_tax.withholding_tax_pnd1_401n"
                ).id,
            },
        )
        cls.cert_pnd3 = cls._create_withholding_tax("pnd3")
        cls.cert_pnd53 = cls._create_withholding_tax(
            "pnd53", partner=cls.partner_b, tax_payer="paid_continue"
        )
        # Create withholding tax wizard
        cls.wht_report_pnd1_wizard = cls._create_wht_wizard("pnd1")
        cls.wht_report_pnd2_wizard = cls._create_wht_wizard("pnd2")
        cls.wht_report_pnd3_wizard = cls._create_wht_wizard("pnd3")
        cls.wht_report_pnd53_wizard = cls._create_wht_wizard("pnd53")

    @classmethod
    def _create_date_ranges(cls):
        generator = cls.env["date.range.generator"].create(
            {
                "date_start": "2026-01-01",
                "name_prefix": "2026/Test/M-",
                "type_id": cls.date_range_type.id,
                "duration_count": 1,
                "unit_of_time": str(MONTHLY),
                "count": 12,
            }
        )
        generator.action_apply()

    @classmethod
    def _create_withholding_tax(
        cls, income_tax_form, partner=None, tax_payer=None, line_vals=None
    ):
        """Pay a vendor bill with withholding tax and confirm its certificate"""
        bill = cls._create_th_invoice(
            "in_invoice",
            [(100.0, cls.wht_tax)],
            partner=partner,
            post=True,
            fill_tax_invoice=True,
        )
        payment = (
            cls.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=bill.ids)
            .create(
                {
                    "payment_date": bill.date,
                    "withhold": "withhold_pay",
                    "journal_id": cls.bank_journal.id,
                    "payment_method_line_id": cls.outbound_payment_method_line.id,
                }
            )
            ._create_payments()
        )
        payment.action_create_wht_cert()
        cert = payment.wht_cert_ids
        cert.income_tax_form = income_tax_form
        if tax_payer:
            cert.tax_payer = tax_payer
        if line_vals:
            cert.wht_line.write(line_vals)
        cert.action_done()
        return cert

    @classmethod
    def _create_wht_wizard(cls, income_tax_form):
        return cls.wht_wizard_obj.create(
            {
                "income_tax_form": income_tax_form,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
                "show_cancel": False,
            }
        )

    def test_01_wht_button_export_html(self):
        # Test onchange date range
        self.assertEqual(
            self.wht_report_pnd3_wizard.date_from, self.date_range.date_start
        )
        self.assertEqual(self.wht_report_pnd3_wizard.date_to, self.date_range.date_end)
        with Form(self.wht_report_pnd3_wizard) as f:
            f.date_range_id = self.last_date_range
        self.assertEqual(
            self.wht_report_pnd3_wizard.date_from, self.last_date_range.date_start
        )
        self.assertEqual(
            self.wht_report_pnd3_wizard.date_to, self.last_date_range.date_end
        )
        # Check date from > date to, it should error
        with self.assertRaises(UserError), Form(self.wht_report_pnd3_wizard) as f:
            f.date_from = "2020-01-05"
            f.date_to = "2020-01-01"

        report = self.wht_report_pnd3_wizard.button_export_html()
        self.assertEqual(report["name"], "Withholding Tax Report")
        self.assertEqual(report["report_type"], "qweb-html")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )

        # Check file download should name tax + date (B.E. year, last range)
        report_name = self.wht_report_pnd3_wizard._get_report_base_filename()
        self.assertEqual(report_name, "WHT-P03-256912")

    def test_02_wht_button_export_pdf_std(self):
        report = self.wht_report_pnd3_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["wht_report_data"]), 1)
        self.assertFalse(res_data["wht_groupby_partner"])
        self.assertEqual(res_data["wht_report_format"], "std")
        line = res_data["wht_report_data"][0]
        self.assertEqual(line["cert_id"][0], self.cert_pnd3.id)
        self.assertEqual(line["base"], 100.0)
        self.assertEqual(line["amount"], 3.0)
        self.assertEqual(line["partner_name"], self.partner_a.display_name)
        # Title of an individual (Thai if installed), no branch
        self.assertIn(line["partner_title"], ("Mr.", "นาย"))
        self.assertFalse(line["partner_branch"])
        self.assertEqual(res_data["total_base"], 100.0)
        self.assertEqual(res_data["total_wht"], 3.0)
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_th_account_tax_report.report_withholding_tax",
            self.wht_report_pnd3_wizard.ids,
        )[0]
        self.assertIn(b'res-model="res.partner"', html)
        self.assertIn(f'res-id="{self.partner_a.id}"'.encode(), html)
        self.assertEqual(report["name"], "Withholding Tax Report")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )
        # PDF with a specific engine (v20 report format)
        self.env.ref(
            "l10n_th_account_tax_report.action_print_report_wht_qweb"
        ).report_type = "qweb-pdf-wkhtmltopdf"
        report = self.wht_report_pnd3_wizard.button_export_pdf()
        self.assertEqual(report["report_type"], "qweb-pdf-wkhtmltopdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )
        # Cancelled certificate is shown only with "Show Cancelled"
        self.cert_pnd3.action_cancel()
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        self.assertFalse(res_data["wht_report_data"])
        self.wht_report_pnd3_wizard.show_cancel = True
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        self.assertEqual(res_data["wht_report_data"][0]["partner_name"], "Cancelled")
        # Render the report
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_th_account_tax_report.report_withholding_tax",
            self.wht_report_pnd3_wizard.ids,
        )[0]
        self.assertIn(b"Withholding Tax Report", html)
        self.assertIn(b'res-model="withholding.tax.cert"', html)
        self.assertIn(f'res-id="{self.cert_pnd3.id}"'.encode(), html)
        # No partner link on a cancelled certificate
        self.assertNotRegex(html, rb'res-model="res.partner"[^>]*res-id=')

    def test_03_wht_button_export_pdf_rd(self):
        # Check change config standard to rd
        self.env.company.wht_report_format = "rd"
        report = self.wht_report_pnd3_wizard.button_export_pdf()

        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])

        # Get data query tax is 1
        self.assertEqual(len(res_data["wht_report_data"]), 1)
        self.assertEqual(len(res_data["rd_pages"]), 1)
        page = res_data["rd_pages"][0]
        line = res_data["wht_report_data"][0]
        self.assertEqual(page["lines"], [line])
        self.assertEqual(page["total_base"], line["base"])
        self.assertEqual(page["total_wht"], line["amount"])
        # Long texts are written smaller to fit their box of the form
        self.assertFalse(line["rd_styles"])
        self.partner_a.street = "999/123 หมู่ที่ 5 อาคารสาทรซิตี้ทาวเวอร์ ชั้น 25 " * 2
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        self.assertIn(
            "font-size",
            res_data["rd_pages"][0]["lines"][0]["rd_styles"]["partner_address"],
        )
        # Too long at the minimum size: shortened
        self.partner_a.street *= 5
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        address = res_data["rd_pages"][0]["lines"][0]["partner_address"]
        self.assertTrue(address.endswith("…"))
        self.assertFalse(res_data["wht_groupby_partner"])
        self.assertEqual(res_data["wht_report_format"], "rd")
        self.assertEqual(report["name"], "Withholding Tax Report (RD)")
        self.assertEqual(report["report_type"], "qweb-pdf")
        self.assertEqual(
            report["report_name"],
            f"l10n_th_account_tax_report.report_rd_withholding_tax/{self.wht_report_pnd3_wizard.id}",
        )
        # Print from the HTML view (standard report) gives the RD form too
        content, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            "l10n_th_account_tax_report.report_withholding_tax",
            self.wht_report_pnd3_wizard.ids,
        )
        self.assertIn(b"o_report_rd_withholding_tax_report_pnd3", content)

        # Allow group by partner by filter PND1A or send context need_group_by_partner=1
        res_data = (
            self.env["report.l10n_th_account_tax_report.report_rd_withholding_tax"]
            .with_context(need_group_by_partner=1)
            ._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        )
        self.assertEqual(len(res_data["wht_groupby_partner"]), 1)
        # Render the RD forms
        self.partner_a.vat = False
        for wizard in (
            self.wht_report_pnd1_wizard,
            self.wht_report_pnd3_wizard,
            self.wht_report_pnd53_wizard,
        ):
            html = self.env["ir.actions.report"]._render_qweb_html(
                "l10n_th_account_tax_report.report_rd_withholding_tax", wizard.ids
            )[0]
            self.assertTrue(html)
            self.assertIn(b'res-model="withholding.tax.cert"', html)
            self.assertIn(b'res-model="res.partner"', html)

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
        content, file_type = model.create_xlsx_report(
            self.wht_report_pnd3_wizard.ids, data=report["data"]
        )
        self.assertEqual(file_type, "xlsx")
        self.assertTrue(content)

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
        # Date in B.E. (ddmmyyyy)
        self.assertIn("|15012569|", res_data["text_file_value"])
        # Rate with 2 decimals, as the RD text file format
        self.assertIn("|3.00|", res_data["text_file_value"])

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
        # Tax ID and branch of a juristic person
        self.assertIn("|0105555123450|00001|", res_data["text_file_value"])
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

        # Bank account of income 4A in the data lines
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax"
        ]._get_report_values(self.wht_report_pnd53_wizard.ids, report["data"])
        bank_accounts = [
            line["partner_bank_account"]
            for line in res_data["wht_report_data"]
            if line["wht_cert_income_type"] == "4A"
        ]
        self.assertEqual(bank_accounts, [self.bank_partner.sanitized_account_number])

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

    def test_09_wht_button_export_text_file_not_available(self):
        """The text file needs a format of the form, set in the settings"""
        self.assertTrue(self.wht_report_pnd3_wizard.can_export_txt)
        self.assertFalse(self.wht_report_pnd2_wizard.can_export_txt)
        with self.assertRaisesRegex(UserError, "not available for PND2"):
            self.wht_report_pnd2_wizard.button_export_txt()
        self.env.company.wht_text_file_pnd3_format = False
        with self.assertRaisesRegex(UserError, "Set the text file format of PND3"):
            self.wht_report_pnd3_wizard.button_export_txt()

    def test_10_wht_rate_format(self):
        """Rates show their decimals only: 3%, 1.5%; the RD text file has 2"""
        report = self.env["report.l10n_th_account_tax_report.report_withholding_tax"]
        for rate, text in ((3.0, "3%"), (1.5, "1.5%"), (2.75, "2.75%"), (0.0, "0%")):
            self.assertEqual(report._format_wht_rate(rate), text)
        report_text = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax_text"
        ]
        self.assertEqual(report_text._format_wht_textfile_rate(3.0), "3.00")
        self.assertEqual(report_text._format_wht_textfile_rate(2.75), "2.75")
        # No thousands separator, the RD format forbids commas
        self.assertEqual(report_text._format_wht_textfile_amount(1750.0), "1750.00")
        self.assertEqual(report_text._format_wht_textfile_amount(False), "0.00")
        with self.assertRaises(UserError):
            report_text._format_wht_textfile_rate(1.125)
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_th_account_tax_report.report_withholding_tax",
            self.wht_report_pnd3_wizard.ids,
        )[0]
        self.assertIn(b"<span>3%</span>", html)

    def test_11_wht_partner_names(self):
        """RD asks the first name only, then the middle name and the surname"""
        self.partner_a.write({"firstname": "สมชาย", "lastname": "ณ อยุธยา"})
        report = self.wht_report_pnd3_wizard.button_export_txt()
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_withholding_tax_text"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        self.assertIn("|สมชาย|ณ อยุธยา|", res_data["text_file_value"])
        res_data = self.env[
            "report.l10n_th_account_tax_report.report_rd_withholding_tax"
        ]._get_report_values(self.wht_report_pnd3_wizard.ids, report["data"])
        line = res_data["rd_pages"][0]["lines"][0]
        self.assertEqual(line["partner_firstname"], "สมชาย")
        self.assertEqual(line["partner_lastname"], "ณ อยุธยา")
        # A juristic person keeps its full name
        self.partner_b.name = "บริษัท ทดสอบ จำกัด"
        self.assertEqual(
            self.partner_b._get_tax_report_names(), ("บริษัท ทดสอบ จำกัด", "")
        )
        # An individual without last name, or without first name as created
        # with its name only, has its full name as first name
        partner = self.env["res.partner"].create({"name": "Somchai"})
        self.assertEqual(partner._get_tax_report_names(), ("Somchai", ""))
        partner.write({"firstname": False, "lastname": "สมหญิง ใจดี"})
        self.assertEqual(partner._get_tax_report_names(), ("สมหญิง ใจดี", ""))
