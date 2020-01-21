# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import time

from odoo.tests.common import SavepointCase
from odoo.tools import test_reports
from datetime import date


class TestBankStatementReport(SavepointCase):

    def setUp(self):
        super(TestBankStatementReport, self).setUp()
        self.company_id = self.env.ref('base.main_company')
        self.date_from = time.strftime('2019-01-01')
        self.date_to = time.strftime('2019-12-31')
        self.journal_model = self.env['account.journal']

        self.data_type = self.env['date.range.type'].create({
            'name': 'Fiscal year',
            'company_id': False,
            'allow_overlap': False
        })
        self.date_range_id = self.env['date.range'].create({
            'name': 'FS2019',
            'date_start': '2019-01-01',
            'date_end': '2019-12-31',
            'type_id': self.data_type.id,
        })
        self.journal_account = self.journal_model.search([
            ('type', '=', 'bank')], limit=1)

        # Get data to excel
        self.xlsx_report_name = 'bank_statement_xlsx'
        self.report = self.env['report.bank.statement'].create({
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'bank_account_id': self.journal_account.id,
            })
        self.report._compute_results()

    def test_xlsx(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.xlsx_report_name,
                                [self.report.id],
                                report_type='xlsx')

    def test_validate_date(self):
        self.company_id.write({
            'fiscalyear_last_day': 31,
            'fiscalyear_last_month': 12,
        })
        user = self.env.ref('base.user_root').with_context(
            company_id=self.company_id.id)
        wizard = self.env['bank.statement.report.wizard'].with_context(
            user=user.id
        )
        self.assertEqual(wizard._init_date_from(),
                         time.strftime('%Y') + '-01-01')

    def test_validate_date_range(self):
        wizard = self.env['bank.statement.report.wizard'].create({
            'date_range_id': self.date_range_id.id,
            'bank_account_id': self.journal_account.id,
        })
        wizard.onchange_date_range_id()
        self.assertEqual(wizard.date_from, date(2019, 1, 1))
        self.assertEqual(wizard.date_to, date(2019, 12, 31))

    def test_get_report_html(self):
        self.report.get_html(given_context={
            'active_id': self.report.id
            })

    def test_bank_statement_report_wizard(self):
        wizard = self.env['bank.statement.report.wizard'].create({
            'date_range_id': self.date_range_id.id,
            'bank_account_id': self.journal_account.id,
        })
        wizard._export('qweb-pdf')
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
