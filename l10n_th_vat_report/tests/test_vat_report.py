from odoo.tests.common import SingleTransactionCase
from odoo.tests.common import Form


class TestVatReport(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestVatReport, cls).setUpClass()
        cls.date_range_type = cls.env['date.range.type'].search(
            [], order="id desc", limit=1)
        if not cls.date_range_type:
            cls.date_range_type = cls.env['date.range.type'].create(
                {'name': 'Year2019'})
        cls.date_range = cls.env['date.range'].search(
            [], order="id desc", limit=1)
        if not cls.date_range:
            cls.date_range = cls.env['date.range'].create(
                {'name': '01/2019', 'type_id': cls.date_range_type.id,
                 'date_start': '2019-01-01', 'date_end': '2019-01-31'})

    def test_vat_report(self):
        f = Form(self.env['report.vat'])
        f.tax_id = self.env['account.tax'].search([('id', '=', 1)])
        f.date_range_id = self.date_range
        wizard = f.save()
        wizard.XLSX()
        wizard.PDF()
        wizard.VAT_Report()
