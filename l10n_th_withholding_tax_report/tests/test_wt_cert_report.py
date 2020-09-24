# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time

from odoo import fields
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestWithholdingTaxReport(common.TransactionCase):
    def setUp(self):
        super().setUp()
        Journal = self.env["account.journal"]
        Account = self.env["account.account"]
        DateRange = self.env["date.range"]
        DateRangeType = self.env["date.range.type"]
        Payment = self.env["account.payment"]
        WTCert = self.env["withholding.tax.cert"]
        WTCertLine = self.env["withholding.tax.cert.line"]
        Report = self.env["ir.actions.report"]
        self.report_name = "withholding.tax.report.xlsx"
        self.report = Report._get_report_from_name(self.report_name)
        self.model = self.env["withholding.tax.report"]
        self.wizard = self.env["withholding.tax.report.wizard"]
        receivable_account = self.env.ref("account.data_account_type_receivable")
        payable_account = self.env.ref("account.data_account_type_payable")
        self.partner_id = self.env.ref("base.res_partner_12")
        self.company_id = self.env.ref("base.main_company")
        self.date_from = time.strftime("%Y-%m-01")
        self.date_to = time.strftime("%Y-%m-28")

        self.journal_bank = Journal.search([("type", "=", "bank")], limit=1)
        if not self.journal_bank:
            self.journal_bank = Journal.create(
                {"name": "Bank", "type": "bank", "code": "BNK67"}
            )

        self.account_receivable = Account.search(
            [("user_type_id", "=", receivable_account.id)], limit=1,
        )
        if not self.account_receivable:
            self.account_receivable = Account.create(
                {
                    "code": 11111990,
                    "name": "Receivable Test",
                    "user_type_id": receivable_account.id,
                    "reconcile": True,
                }
            )
        self.account_payable = Account.search(
            [("user_type_id", "=", payable_account.id)], limit=1,
        )
        if not self.account_payable:
            self.account_payable = Account.create(
                {
                    "code": 21111990,
                    "name": "Payable Test",
                    "user_type_id": payable_account.id,
                    "reconcile": True,
                }
            )
        if not self.partner_id.property_account_receivable_id:
            self.partner_id.write(
                {
                    "property_account_receivable_id": self.account_receivable.id,
                    "property_account_payable_id": self.account_payable.id,
                }
            )

        # Create date_range
        self.type = DateRangeType.create(
            {"name": "Month", "company_id": False, "allow_overlap": False}
        )
        self.date_range_id = DateRange.create(
            {
                "name": "FiscalYear",
                "date_start": self.date_from,
                "date_end": self.date_to,
                "type_id": self.type.id,
            }
        )

        # Create Withholding Tax
        payment = Payment.create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "payment_method_id": 2,
                "partner_id": self.partner_id.id,
                "amount": 100.0,
                "journal_id": self.journal_bank.id,
            }
        )
        payment.post()
        self.withholding_tax = WTCert.create(
            {
                "payment_id": payment.id,
                "income_tax_form": "pnd3",
                "date": fields.Date.today(),
                "supplier_partner_id": self.partner_id.id,
            }
        )
        WTCertLine.create(
            {
                "cert_id": self.withholding_tax.id,
                "wt_cert_income_type": "1",
                "wt_percent": 3.0,
                "amount": 100.0,
                "base": 3333.33,
            }
        )
        # compute_results
        self.base_filters = self._getBaseFilters(self.date_range_id)
        self.withholding_tax_report = self.model.create(self.base_filters)
        self.withholding_tax_report._compute_results()

    def _getBaseFilters(self, date_range):
        return {
            "company_id": self.env.user.company_id.id,
            "income_tax_form": "pnd3",
            "date_range_id": date_range.id,
            "date_from": date_range.date_start,
            "date_to": date_range.date_end,
        }

    def test_01_withholding_tax_report(self):
        report = self.wizard.create(
            {"income_tax_form": "pnd3", "date_range_id": self.date_range_id.id}
        )
        report.button_export_html()
        report.button_export_pdf()
        report.button_export_xlsx()
        report.button_export_txt()

    def test_02_create_text_file(self):
        text = self.withholding_tax_report._create_text(self.withholding_tax_report)
        text.split("|")
        self.assertEqual(text[0], "1")

    def test_03_create_xlsx_file(self):
        report = self.report
        self.assertEqual(report.report_type, "xlsx")
        report.render_xlsx(self.withholding_tax_report.id, None)
