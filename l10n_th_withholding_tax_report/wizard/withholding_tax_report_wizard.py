# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class WithHoldingTaxReportWizard(models.TransientModel):
    _name = 'withholding.tax.report.wizard'
    _description = 'Withholding Tax Report Wizard'

    income_tax_form = fields.Selection(
        [('pnd3', 'PND3'),
         ('pnd53', 'PND53')],
        string='Income Tax Form',
        required=True,
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date Range',
        required=True,
    )
    date_from = fields.Date(
        string='Date From',
    )
    date_to = fields.Date(
        string='Date To',
    )

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_th_withholding_tax_report.action_withholding_tax_report')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['withholding.tax.report']
        report = model.create(self._prepare_wt_report())
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    @api.multi
    def button_export_excel(self):
        self.ensure_one()
        report_type = 'excel'
        return self._export(report_type)

    def _prepare_wt_report(self):
        self.ensure_one()
        return {
            'income_tax_form': self.income_tax_form,
            'date_range_id': self.date_range_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['withholding.tax.report']
        report = model.create(self._prepare_wt_report())
        return report.print_report(report_type)
