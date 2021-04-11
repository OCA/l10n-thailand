# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestResCurrencyRateProviderBOT(common.TransactionCase):

    def setUp(self):
        super().setUp()

        self.Company = self.env['res.company']
        self.CurrencyRate = self.env['res.currency.rate']
        self.CurrencyRateProvider = self.env['res.currency.rate.provider']

        self.today = fields.Date.today()
        self.thb_currency = self.env.ref('base.THB')
        self.eur_currency = self.env.ref('base.EUR')
        self.my_company = self.Company.create({
            'name': 'Test Company',
            'currency_id': self.thb_currency.id,
        })
        self.bot_provider = self.CurrencyRateProvider.create({
            'service': 'BOT',
            'currency_ids': [(4, self.eur_currency.id)],
            'company_id': self.my_company.id,
        })
        self.CurrencyRate.search([]).unlink()

    def test_supported_currencies(self):
        supported_currencies = (self.bot_provider._get_supported_currencies())
        self.assertEqual(len(supported_currencies), 48)

    def test_base_curency_not_THB(self):
        self.company1 = self.Company.create({
            'name': 'Test Company EUR',
            'currency_id': self.eur_currency.id,
        })
        self.bot_provider1 = self.CurrencyRateProvider.create({
            'service': 'BOT',
            'currency_ids': [(4, self.thb_currency.id)],
            'company_id': self.company1.id,
        })
        date = self.today - relativedelta(days=1)
        self.bot_provider1._update(date, date)

    def test_update_no_clien_id(self):
        self.my_company.bot_client_id = False
        date = self.today - relativedelta(days=1)
        self.bot_provider._update(date, date)

    def test_update_clien_id_fail(self):
        self.my_company.bot_client_id = 'Test'
        date = self.today - relativedelta(days=1)
        self.bot_provider._update(date, date)
