# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SingleTransactionCase
from odoo.tests.common import Form


class TestWTCert(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestWTCert, cls).setUpClass()
        cls.date_range_type = cls.env['date.range.type'].search(
            [], order="id desc", limit=1)
        if not cls.date_range_type:
            cls.date_range_type = cls.env['date.range.type'].create(
                {'name': 'Year2019'})
        cls.date_range = cls.env['date.range'].search(
            [], order="id desc", limit=1)
        if not cls.date_range:
            cls.date_range = cls.env['date.range'].create(
                {'name': '05/2019', 'type_id': cls.date_range_type.id,
                 'date_start': '2019-05-01', 'date_end': '2019-05-31'})
        cls.report_pnd_template = cls.env['xlsx.template'].search([
            ('fname', '=', 'xlsx_report_pnd.xlsx')])
        cls.report_pnd_txt_template = cls.env['xlsx.template'].search([
            ('fname', '=', 'xlsx_report_pnd_txt.xlsx')])
        cls.report_vat_template = cls.env['xlsx.template'].search([
            ('fname', '=', 'report_vat.xlsx')])

    def test_1_wt_cert_report_pnd(self):
        # Generate WT Cert PND Report Action Wizard
        f = Form(self.env['report.pnd'])
        f.income_tax_form = 'pnd3'
        f.date_range_id = self.date_range
        f.template_id = self.report_pnd_template
        wizard = f.save()
        wizard.report_xlsx()

        # Generate WT Cert PND Text Report Action Wizard
        f = Form(self.env['report.pnd'])
        f.income_tax_form = 'pnd3'
        f.date_range_id = self.date_range
        f.template_id = self.report_pnd_txt_template
        wizard = f.save()
        wizard.report_xlsx()

    def test_2_vat_report(self):
        # Generate WT Cert VAT Report Action Wizard
        f = Form(self.env['report.vat'])
        f.tax_id = self.env['account.tax'].search([('id', '=', 1)])
        f.date_range_id = self.date_range
        f.template_id = self.report_vat_template
        wizard = f.save()
        wizard.report_xlsx()
