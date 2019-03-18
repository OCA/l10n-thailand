# -*- coding: utf-8 -*-
from odoo import models, api
from num2words import num2words


class ReportWithholdingTaxCert(models.AbstractModel):
    _name = 'report.withholding_tax_pdf'
    _description = 'Withholding tax cert report with pdf preprint'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'withholding_tax_pdf')
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'report_type': data.get('report_type') if data else '',
        }


class WithholdingTaxCert(models.Model):
    _inherit = 'withholding.tax.cert'

    @api.multi
    def amount_text(self, amount):
        try:
            return num2words(amount, to='currency', lang='th')
        except NotImplementedError:
            return num2words(amount, to='currency', lang='en')
