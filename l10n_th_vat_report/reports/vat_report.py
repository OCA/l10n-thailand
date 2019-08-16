# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class VatReportView(models.TransientModel):
    _name = 'vat.report.view'
    _inherit = 'account.move.line'
    _order = 'id'

    base_amount = fields.Monetary(
        currency_field='currency_id',
    )
    tax_amount = fields.Monetary(
        currency_field='currency_id',
    )
    tax_date = fields.Char()


class VatReport(models.TransientModel):
    _name = 'report.vat.report'

    # Filters fields, used for data computation
    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
    )
    date_from = fields.Date()
    date_to = fields.Date()

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='vat.report.view',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        self._cr.execute("""
            SELECT aml.id as id, am.company_id, am.name, aml.account_id,
                aml.tax_invoice, aml.partner_id, aml.date, aml.tax_date,
                aml.tax_base_amount as base_amount, aml.balance tax_amount
            FROM account_move_line aml
            JOIN account_move am on aml.move_id = am.id
            WHERE tax_line_id is not null and aml.date >= %s and aml.date <= %s
                and aml.company_id = %s and aml.account_id = %s
            ORDER BY aml.tax_date
        """, (self.date_from, self.date_to, self.company_id.id,
              self.account_id.id))
        vat_report_results = self._cr.dictfetchall()
        ReportLine = self.env['vat.report.view']
        for line in vat_report_results:
            self.results += ReportLine.new(line)

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'l10n_th_vat_report.report_vat_report_xlsx'
        else:
            report_name = 'l10n_th_vat_report.report_vat_report_pdf'
        context = dict(self.env.context)
        action = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1)
        return action.with_context(context).report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'l10n_th_vat_report.report_vat_report_html').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
