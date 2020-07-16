# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestHolidays(TransactionCase):

    def setUp(self):
        super(TestHolidays, self).setUp()
        self.holiday_model = self.env['hr.holidays.public']
        self.wizard_next_year = self.env['public.holidays.next.year.wizard']

        self.template_id = self.env.ref('l10n_th_holidays.th_holidays_public')

    def test_create_public_holidays(self):
        public_holidays_before = len(self.holiday_model.search([]))
        wizard = self.wizard_next_year.create({
            'template_id': self.template_id.id,
            'year': self.template_id.year + 1,
        })
        wizard.create_public_holidays()
        public_holidays_after = len(self.holiday_model.search([]))
        self.assertNotEqual(public_holidays_before, public_holidays_after)
