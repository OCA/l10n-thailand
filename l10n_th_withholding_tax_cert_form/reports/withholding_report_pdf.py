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

    @api.multi
    def _compute_sum_type_other(self, lines, type):
        base_type_other = sum(lines.filtered(
            lambda l: l.wt_cert_income_type in ['6', '7', '8']).mapped(type))
        return base_type_other

    @api.multi
    def _compute_desc_type_other(self, lines, type):
        base_type_other = lines.filtered(
            lambda l: l.wt_cert_income_type in ['6', '7', '8']).mapped(type)
        desc = ", ".join(base_type_other)
        return desc
