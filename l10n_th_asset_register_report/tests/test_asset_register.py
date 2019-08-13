# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import time

from odoo.tests.common import SavepointCase
from datetime import date


class TestAssetRegisterReport(SavepointCase):

    def setUp(self):
        super(TestAssetRegisterReport, self).setUp()
        self.asset_model = self.env['account.asset']
        self.asset_profile_model = self.env['account.asset.profile']
        self.account_account_model = self.env['account.account']
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
            ('user_type_id', '=',
                self.env.ref('account.data_account_type_fixed_assets').id)],
                limit=1)
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
        self.asset_view = self.asset_model.create({
            'name': 'View',
            'type': 'view',
            'purchase_value': 0,
        })
        self.asset_profile_id = self.asset_profile_model.create({
            'name': 'Equipment',
            'parent_id': self.asset_view.id,
            'journal_id': self.expenses_journal.id,
            'account_asset_id': self.account_asset.id,
            'account_depreciation_id': self.account_accum_depre.id,
            'account_expense_depreciation_id': self.account_depreciation.id,
            'method': 'linear',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'year',
        })
        self.asset_id = self.asset_model.search(
            [('type', '!=', 'view')], limit=1)
        if not self.asset_id:
            self.asset_id = self.asset_model.create({
                'name': 'Table',
                'parent_id': self.asset_view.id,
                'type': 'normal',
                'purchase_value': 100000,
                'salvage_value': 1000,
                'date_start': '2019-01-01',
                'profile_id': self.asset_profile_id.id,
            })

    def test_validate_date(self):
        company_id = self.env.ref('base.main_company')
        company_id.write({
            'fiscalyear_last_day': 31,
            'fiscalyear_last_month': 12,
        })
        user = self.env.ref('base.user_root').with_context(
            company_id=company_id.id)
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

    def test_asset_report(self):
        wizard = self.env['asset.register.report.wizard'].create({
            'date_range_id': self.date_range_id.id,
            'accum_depre_account_type': self.accum_depre_type.id,
            'depre_account_type': self.depre_type.id,
        })
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
