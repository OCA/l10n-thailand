# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time
from datetime import date
from odoo.tests import common
from odoo.tools import test_reports

_logger = logging.getLogger(__name__)


class TestVat(common.TransactionCase):

    def setUp(cls):
        super(TestVat, cls).setUp()

        cls.model = cls._getReportModel()

        cls.qweb_report_name = cls._getQwebReportName()
        cls.xlsx_report_name = cls._getXlsxReportName()
        cls.xlsx_action_name = cls._getXlsxReportActionName()

        cls.report_title = cls._getReportTitle()

        cls.base_filters = cls._getBaseFilters()

        cls.report = cls.model.create(cls.base_filters)
        cls.report._compute_results()

    def test_html(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.qweb_report_name,
                                [self.report.id],
                                report_type='qweb-html')

    def test_qweb(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.qweb_report_name,
                                [self.report.id],
                                report_type='qweb-pdf')

    def test_xlsx(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.xlsx_report_name,
                                [self.report.id],
                                report_type='xlsx')

    def test_print(self):
        self.report.print_report('qweb')
        self.report.print_report('xlsx')

    def _getReportModel(self):
        return self.env['report.vat.report']

    def _getQwebReportName(self):
        return 'l10n_th_vat_report.report_vat_report_pdf'

    def _getXlsxReportName(self):
        return 'l10n_th_vat_report.report_vat_report_xlsx'

    def _getXlsxReportActionName(self):
        return 'l10n_th_vat_report.action_vat_report_xlsx'

    def _getReportTitle(self):
        return 'VAT Report'

    def _getBaseFilters(self):
        tax_id = self.env['account.tax'].search([('id', '=', 1)])
        date_start = time.strftime('%Y-01-01')
        date_end = time.strftime('%Y-12-31')

        # Create date_range
        date_range = self.env['date.range']
        self.type = self.env['date.range.type'].create(
            {'name': 'Year',
             'company_id': False,
             'allow_overlap': False})
        self.date_range_id = date_range.create({
            'name': 'FiscalYear',
            'date_start': date_start,
            'date_end': date_end,
            'type_id': self.type.id,
        })

        return {
            'company_id': self.env.user.company_id.id,
            'tax_id': tax_id.id,
            'account_id': tax_id.account_id.id,
            'date_range_id': self.date_range_id.id,
            'date_from':  date_start,
            'date_to': date_end,
            }


class TestVatReport(common.TransactionCase):

    def setUp(self):
        super(TestVatReport, self).setUp()
        self.date_from = time.strftime('%Y-%m-01')
        self.date_to = time.strftime('%Y-%m-28')
        self.company_id = self.env.ref('base.main_company')

        # Create Tax
        self.tax_account_id = self.env['account.account'].create({
            'name': 'Tax Paid',
            'code': 'TAXTEST',
            'user_type_id': self.env.ref(
                'account.data_account_type_current_liabilities'
            ).id,
        }).id
        self.tax_id = self.env['account.tax'].create({
            'name': 'Test Tax 10.0%',
            'amount': 10.0,
            'amount_type': 'percent',
            'account_id': self.tax_account_id,
        })

        # Create date_range
        date_range = self.env['date.range']
        self.type = self.env['date.range.type'].create(
            {'name': 'Month',
             'company_id': False,
             'allow_overlap': False})
        self.date_range_id = date_range.create({
            'name': 'FiscalYear',
            'date_start': self.date_from,
            'date_end': self.date_to,
            'type_id': self.type.id,
        })

    def test_get_report_html(self):
        report = self.env['report.vat.report'].create({
            'company_id': self.company_id.id,
            'tax_id': self.tax_id.id,
            'account_id': self.tax_account_id,
            'date_range_id': self.date_range_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            })
        report._compute_results()
        report.get_html(given_context={
            'active_id': report.id
            })

    def test_wizard(self):
        wizard = self.env['l10n.vat.report.wizard'].create({
            'company_id': self.company_id.id,
            'tax_id': self.tax_id.id,
            'account_id': 1,
            'date_range_id': self.date_range_id.id,
            'date_from': self.date_to,
            'date_to': self.date_from,
            })
        wizard._onchange_tax_id()
        wizard._onchange_date_range_id()

        # Test _onchange_tax_id
        self.assertEqual(wizard.account_id.id, wizard.tax_id.account_id.id)

        # Test _onchange_date_range_id
        self.assertEqual(wizard.date_from, date(
            date.today().year, date.today().month, 1))
        self.assertEqual(wizard.date_to, date(
            date.today().year, date.today().month, 28))

        wizard._export('qweb-pdf')
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
