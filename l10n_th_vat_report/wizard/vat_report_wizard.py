# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class VatReportWizard(models.TransientModel):
    _name = 'l10n.vat.report.wizard'
    _description = 'Wizard for VAT Report'
    # Search Criteria
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        required=True,
        ondelete='cascade',
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        required=True,
        domain=[('tax_exigibility', '=', 'on_invoice'),
                ('type_tax_use', 'in', ['sale', 'purchase']),
                ('include_base_amount', '=', False)],
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        required=True,
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Period',
        required=True,
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
    )

    @api.onchange('tax_id')
    def _onchange_tax_id(self):
        self.account_id = self.tax_id.account_id

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_th_vat_report.action_report_vat_report_html')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report.vat.report']
        report = model.create(self._prepare_vat_report())
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

    def _prepare_vat_report(self):
        self.ensure_one()
        return {
            'company_id': self.company_id.id,
            'tax_id': self.tax_id.id,
            'account_id': self.account_id.id,
            'date_range_id': self.date_range_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }

    def _export(self, report_type):
        model = self.env['report.vat.report']
        report = model.create(self._prepare_vat_report())
        return report.print_report(report_type)
