# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class VatReportView(models.TransientModel):
    _name = 'vat.report.view'
    _description = 'Vat Report View'
    _inherit = 'account.move.line'
    _order = 'id'

    tax_base_amount = fields.Float()
    tax_amount = fields.Float()
    tax_date = fields.Char()


class VatReport(models.TransientModel):
    _name = 'report.vat.report'
    _description = 'Report Vat Report'

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
                CASE WHEN ai.type in ('out_refund', 'in_refund')
                then -aml.tax_base_amount
                else aml.tax_base_amount end as tax_base_amount,
                CASE WHEN aa.internal_group = 'asset'
                then aml.balance else -aml.balance end as tax_amount
            FROM account_move_line aml
            JOIN account_move am on aml.move_id = am.id
            JOIN account_account aa on aa.id = aml.account_id
            LEFT JOIN account_invoice ai on ai.id = aml.invoice_id
            WHERE aml.tax_line_id is not null and aml.date >= %s and
                aml.date <= %s and aml.company_id = %s and
                aml.account_id = %s and am.state = 'posted'
            ORDER BY aml.tax_date, am.name
        """, (self.date_from, self.date_to, self.company_id.id,
              self.account_id.id))
        vat_report_results = self._cr.dictfetchall()
        ReportLine = self.env['vat.report.view']
        for line in vat_report_results:
            self.results += ReportLine.new(line)

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        action = report_type == 'xlsx' and self.env.ref(
            'l10n_th_vat_report.action_vat_report_xlsx') or \
            self.env.ref('l10n_th_vat_report.action_vat_report_pdf')
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'l10n_th_vat_report.report_vat_report_html').render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
