# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import datetime

from dateutil.rrule import MONTHLY

from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.l10n_th_gov_purchase_request.tests.test_gov_purchase_request import (
    TestGovPurchaseRequest,
)


@tagged("post_install", "-at_install")
class TestGovPurchaseReport(TestGovPurchaseRequest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date_range_obj = cls.env["date.range"]
        cls.sheet_obj = cls.env["hr.expense.sheet"]
        cls.purchase_agreement_obj = cls.env["purchase.requisition"]
        cls.purchase_report_wizard = cls.env["purchase.report.wizard"]
        cls.non_purchase_report_wizard = cls.env["non.purchase.report.wizard"]
        cls.purchase_tracking_report_wizard = cls.env["purchase.tracking.report.wizard"]
        cls.common_purchase_report = cls.env["common.purchase.report.xlsx"]
        cls.company = cls.env.company

        cls.product = cls.env.ref("l10n_th_gov_purchase_request.product_type_001")
        cls.partner1 = cls.env.ref("base.res_partner_12")
        cls.employee1.address_home_id = cls.partner1.id
        cls.purchase_type1 = cls.env.ref(
            "l10n_th_gov_purchase_request.purchase_type_001"
        )

        # Activate Multi Currency
        cls.usd_currency = cls.env.ref("base.USD")
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.eur_currency.active = True

        # Create date range
        cls._create_date_range(cls)
        cls.date_range = cls.date_range_obj.search([], limit=1, order="date_start asc")
        cls.last_date_range = cls.date_range_obj.search(
            [], limit=1, order="date_start desc"
        )
        cls.po_report_wiz = cls.purchase_report_wizard.create(
            {
                "company_id": cls.company.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )
        cls.non_po_report_wiz = cls.non_purchase_report_wizard.create(
            {
                "company_id": cls.company.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )
        cls.po_tracking_wiz = cls.purchase_tracking_report_wizard.create(
            {
                "company_id": cls.company.id,
                "date_from": cls.date_range.date_start,
                "date_to": cls.date_range.date_end,
            }
        )

    def _create_purchase_request(self, currency, date, purchase_type):
        purchase_request = self.purchase_request_model.create(
            {
                "procurement_type_id": self.procurement_type1.id,
                "procurement_method_id": self.procurement_method1.id,
                "purchase_type_id": purchase_type.id,
                "date_start": date,
                "currency_id": currency.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "product_uom_id": self.product.uom_id.id,
                            "estimated_cost": 100.0,
                            "product_qty": 1,
                        },
                    )
                ],
            }
        )
        # Create committees
        self.procurement_committee_model.create(
            [
                {
                    "name": "Chairman",
                    "approve_role": "chairman",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
                {
                    "name": self.employee2.display_name,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
                {
                    "name": self.employee3.display_name,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
            ]
        )
        # Assign employee as committee
        purchase_request.work_acceptance_committee_ids[0].employee_id = self.employee1
        purchase_request.button_to_approve()
        purchase_request.with_context(to_substate_sequence=20).action_to_substate()
        purchase_request.button_approved()
        return purchase_request

    def _create_po_from_pr(self, purchase_request):
        # Create purchase agreement from purchase request
        wiz = self.wiz.with_context(
            active_model="purchase.request.line",
            active_ids=[purchase_request.line_ids.id],
            active_id=purchase_request.line_ids.id,
        ).create({})
        wiz.make_purchase_requisition()
        requisition = purchase_request.line_ids.requisition_lines.requisition_id
        # Create Purchase from Agreement
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": self.partner1.id,
                "requisition_id": requisition.id,
            }
        )
        purchase._onchange_requisition_id()
        purchase.button_confirm()
        # Change date approved to within range
        purchase.date_approve = self.date_range.date_start
        return purchase

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

    def test_01_purchase_report(self):
        purchase_request = self._create_purchase_request(
            self.usd_currency, self.date_range.date_start, self.purchase_type1
        )
        # Create Purchase
        self._create_po_from_pr(purchase_request)
        # Test change date range
        with Form(self.po_report_wiz) as po_wiz:
            po_wiz.date_range_id = self.date_range
        po_wiz.save()
        self.assertEqual(self.po_report_wiz.date_from, self.date_range.date_start)
        self.assertEqual(self.po_report_wiz.date_to, self.date_range.date_end)

        # Export Excel
        report = self.po_report_wiz.button_export_xlsx()
        self.assertEqual(report["name"], "Purchase Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"], "l10n_th_gov_purchase_report.report_purchase_xlsx"
        )
        # Test export excel by code
        action = self.env.ref(
            "l10n_th_gov_purchase_report.action_print_report_purchase_xlsx"
        )
        report_xlsx = action._render_xlsx(
            report["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    report["report_name"], str(report["context"]["active_ids"][0])
                ),
                "token": "dummy-because-api-expects-one",
            },
        )
        self.assertEqual(report_xlsx[1], "xlsx")

    def test_02_non_purchase_report(self):
        purchase_request = self._create_purchase_request(
            self.usd_currency, self.date_range.date_start, self.purchase_type1
        )
        # Create expense sheet
        with Form(self.sheet_obj) as s:
            s.name = "Expense test"
            s.employee_id = self.employee1
            s.purchase_request_id = purchase_request
        sheet = s.save()

        self.assertEqual(len(sheet.expense_line_ids), 1)
        self.assertTrue(purchase_request.expense_sheet_ids)
        for expense in sheet.expense_line_ids:
            self.assertEqual(
                expense.purchase_type_id, purchase_request.purchase_type_id
            )
        # Update accounting date on expense is start date
        sheet.accounting_date = self.date_range.date_start
        sheet.action_submit_sheet()
        sheet.approve_expense_sheets()
        sheet.action_sheet_move_create()
        # Test change date range
        with Form(self.non_po_report_wiz) as non_po_wiz:
            non_po_wiz.date_range_id = self.date_range
        non_po_wiz.save()
        self.assertEqual(self.non_po_report_wiz.date_from, self.date_range.date_start)
        self.assertEqual(self.non_po_report_wiz.date_to, self.date_range.date_end)

        # Export Excel
        report = self.non_po_report_wiz.button_export_xlsx()
        self.assertEqual(report["name"], "Non Purchase Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"],
            "l10n_th_gov_purchase_report.report_non_purchase_xlsx",
        )
        # Test export excel by code
        action = self.env.ref(
            "l10n_th_gov_purchase_report.action_print_report_non_purchase_xlsx"
        )
        report_xlsx = action._render_xlsx(
            report["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    report["report_name"], str(report["context"]["active_ids"][0])
                ),
                "token": "dummy-because-api-expects-one",
            },
        )
        self.assertEqual(report_xlsx[1], "xlsx")

    def test_03_purchase_tracking_report(self):
        # Create Purchase Request with Multi Currency
        purchase_request = self._create_purchase_request(
            self.eur_currency, self.date_range.date_start, self.purchase_type1
        )
        self._create_po_from_pr(purchase_request)

        # Test change date range
        with Form(self.po_tracking_wiz) as tracking:
            tracking.date_range_id = self.date_range
        tracking.save()
        self.assertEqual(self.po_tracking_wiz.date_from, self.date_range.date_start)
        self.assertEqual(self.po_tracking_wiz.date_to, self.date_range.date_end)

        # Export Excel
        report = self.po_tracking_wiz.button_export_xlsx()
        self.assertEqual(report["name"], "Purchase Tracking Report XLSX")
        self.assertEqual(report["report_type"], "xlsx")
        self.assertEqual(
            report["report_name"], "l10n_th_gov_purchase_report.report_po_tracking_xlsx"
        )
        # Test export excel by code
        action = self.env.ref(
            "l10n_th_gov_purchase_report.action_print_report_po_tracking_xlsx"
        )
        report_xlsx = action._render_xlsx(
            report["context"]["active_ids"],
            {
                "data": "['/report/xlsx/{}/{}','xlsx']".format(
                    report["report_name"], str(report["context"]["active_ids"][0])
                ),
                "token": "dummy-because-api-expects-one",
            },
        )
        self.assertEqual(report_xlsx[1], "xlsx")

    def test_04_check_format_date(self):
        # Test No format date
        date = datetime.date(2023, 1, 15)
        expected_result = "15012566"
        result = self.common_purchase_report.format_date_dmy(date)
        self.assertEqual(result, expected_result)
        # Test Custom format date
        date = datetime.date(2023, 1, 15)
        custom_format = "{day}-{month}-{year}"
        expected_result = "15-01-2566"
        result = self.common_purchase_report.format_date_dmy(
            date, format_date=custom_format
        )
        self.assertEqual(result, expected_result)
