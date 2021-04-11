# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import time

from odoo.tests.common import SavepointCase
from odoo.tools import test_reports
from datetime import date


class TestAssetRegisterReport(SavepointCase):

    def setUp(self):
        super(TestAssetRegisterReport, self).setUp()
        self.asset_model = self.env['account.asset']
        self.asset_profile_model = self.env['account.asset.profile']
        self.account_account_model = self.env['account.account']
        self.company_id = self.env.ref('base.main_company')
        self.date_from = time.strftime('2019-01-01')
        self.date_to = time.strftime('2019-12-31')

        self.fixed_assets = \
            self.env.ref('account.data_account_type_fixed_assets')
        self.accum_depre_type = self.env['account.account.type'].create({
            'name': 'Accumulated Depreciation',
            'type': 'other',
        })
        self.depre_type = self.env['account.account.type'].create({
            'name': 'Depreciation',
            'type': 'other',
        })
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
        self.expenses_journal = self.env['account.journal'].create({
            'name': 'Test expense journal',
            'type': 'purchase',
            'code': 'EXP',
        })
        self.account_asset = self.account_account_model.search([
            ('user_type_id', '=', self.fixed_assets.id)], limit=1)
        if not self.account_asset:
            self.account_asset = self.account_account_model.create({
                'code': 'asset',
                'name': 'Fixed Asset',
                'user_type_id':
                    self.env.ref('account.data_account_type_fixed_assets').id,
            })

        self.account_accum_depre = self.account_account_model.search(
            [('user_type_id', '=', self.accum_depre_type.id)], limit=1)
        if not self.account_accum_depre:
            self.account_accum_depre = self.account_account_model.create({
                'code': 'accumdepre',
                'name': 'Accumulated Depreciation',
                'user_type_id': self.accum_depre_type.id,
            })

        self.account_depreciation = self.account_account_model.search(
            [('user_type_id', '=', self.depre_type.id)], limit=1)
        if not self.account_depreciation:
            self.account_depreciation = self.account_account_model.create({
                'code': 'depre',
                'name': 'Depreciation',
                'user_type_id': self.depre_type.id,
            })
        self.asset_profile_id = self.asset_profile_model.create({
            'name': 'Equipment',
            'journal_id': self.expenses_journal.id,
            'account_asset_id': self.account_asset.id,
            'account_depreciation_id': self.account_accum_depre.id,
            'account_expense_depreciation_id': self.account_depreciation.id,
            'active': True,
            'method': 'linear',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'year',
        })
        self.asset_id = self.asset_model.search([], limit=1)
        if not self.asset_id:
            self.asset_id = self.asset_model.create({
                'name': 'Table',
                'purchase_value': 100000,
                'salvage_value': 1000,
                'date_start': '2019-01-01',
                'profile_id': self.asset_profile_id.id,
            })
        # Get data to excel
        self.xlsx_report_name = 'asset_register_xlsx'
        self.report = self.env['report.asset.register'].create({
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'asset_status': 'open',
            'asset_ids': self.asset_id,
            'asset_profile_ids': self.asset_profile_id,
            'accum_depre_account_type': self.accum_depre_type.id,
            'depre_account_type': self.depre_type.id,
            })
        self.report._compute_results()

    def test_xlsx(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.xlsx_report_name,
                                [self.report.id],
                                report_type='xlsx')

    def test_print(self):
        self.report.print_report('qweb')
        self.report.print_report('xlsx')

    def test_validate_date(self):
        self.company_id.write({
            'fiscalyear_last_day': 31,
            'fiscalyear_last_month': 12,
        })
        user = self.env.ref('base.user_root').with_context(
            company_id=self.company_id.id)
        wizard = self.env['asset.register.report.wizard'].with_context(
            user=user.id
        )
        self.assertEqual(wizard._init_date_from(),
                         time.strftime('%Y') + '-01-01')

    def test_validate_date_range(self):
        wizard = self.env['asset.register.report.wizard'].create({
            'date_range_id': self.date_range_id.id,
            'accum_depre_account_type': self.accum_depre_type.id,
            'depre_account_type': self.depre_type.id,
        })
        wizard.onchange_date_range_id()
        self.assertEqual(wizard.date_from, date(2019, 1, 1))
        self.assertEqual(wizard.date_to, date(2019, 12, 31))

    def test_get_report_html(self):
        self.report.get_html(given_context={
            'active_id': self.report.id
            })

    def test_asset_report(self):
        wizard = self.env['asset.register.report.wizard'].create({
            'date_range_id': self.date_range_id.id,
            'accum_depre_account_type': self.accum_depre_type.id,
            'depre_account_type': self.depre_type.id,
        })
        wizard._export('qweb-pdf')
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
