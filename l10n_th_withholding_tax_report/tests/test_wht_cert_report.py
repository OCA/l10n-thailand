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
        self.model = self.env["withholding.tax.report"]
        self.wizard = self.env["withholding.tax.report.wizard"]
        Journal = self.env["account.journal"]
        self.partner_id = self.env.ref("base.res_partner_12")
        self.journal_bank = Journal.search([("type", "=", "bank")])[0]
        if not self.journal_bank:
            self.journal_bank = Journal.create(
                {"name": "Bank", "type": "bank", "code": "BNK67"}
            )

        # Create date_range
        date_range = self.env["date.range"]
        self.type = self.env["date.range.type"].create(
            {"name": "Month", "company_id": False, "allow_overlap": False}
        )
        self.date_from = time.strftime("%Y-%m-01")
        self.date_to = time.strftime("%Y-%m-28")
        self.company_id = self.env.ref("base.main_company")
        self.date_range_id = date_range.create(
            {
                "name": "FiscalYear",
                "date_start": self.date_from,
                "date_end": self.date_to,
                "type_id": self.type.id,
            }
        )

        # Create Withholding Tax
        payment = self.env["account.payment"].create(
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
        self.withholding_tax = self.env["withholding.tax.cert"].create(
            {
                "payment_id": payment.id,
                "income_tax_form": "pnd3",
                "date": fields.Date.today(),
                "supplier_partner_id": self.partner_id.id,
            }
        )
        self.env["withholding.tax.cert.line"].create(
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
