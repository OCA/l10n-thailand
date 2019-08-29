# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
import time


class BankStatementReportWizard(models.TransientModel):
    """Bank Statement report wizard."""

    _name = 'bank.statement.report.wizard'
    _description = 'Bank Statement Report Wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        required=False,
        string='Company'
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_from = fields.Date(
        required=True,
        default=lambda self: self._init_date_from()
    )
    date_to = fields.Date(
        required=True,
        default=fields.Date.context_today
    )
    bank_account_id = fields.Many2one(
        comodel_name='account.journal',
        domain=[('type', '=', 'bank')],
        required=True,
    )

    def _init_date_from(self):
        """set start date to begin of current year if fiscal year running"""
        today = fields.Date.context_today(self)
        cur_month = fields.Date.to_date(today).month
        cur_day = fields.Date.to_date(today).day
        last_fsc_month = self.env.user.company_id.fiscalyear_last_month
        last_fsc_day = self.env.user.company_id.fiscalyear_last_day

        if cur_month < last_fsc_month \
                or cur_month == last_fsc_month and cur_day <= last_fsc_day:
            return time.strftime('%Y-01-01')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'l10n_th_bank_statement_report.action_report_bank_statement')
        action_data = action.read()[0]
        context1 = action_data.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report.bank.statement']
        report = model.create(self._prepare_report_bank_statement())
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        action_data['context'] = context1
        return action_data

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

    def _prepare_report_bank_statement(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id,
            'bank_account_id': self.bank_account_id.id,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report.bank.statement']
        report = model.create(self._prepare_report_bank_statement())
        return report.print_report(report_type)
