# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class BankStatementReport(models.TransientModel):
    _name = 'report.bank.statement'
    _description = 'Report Bank Statement'

    # Filters fields, used for data computation
    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    date_from = fields.Date()
    date_to = fields.Date()
    bank_account_id = fields.Many2one(
        comodel_name='account.journal',
    )
    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='account.move.line',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    def _get_initial(self, field):
        self.ensure_one()
        move_line = self.env['account.move.line'].search(
            [('date_maturity', '<', self.date_from),
             ('journal_id', '=', self.bank_account_id.id),
             ('account_id', 'in',
             [self.bank_account_id.default_debit_account_id.id,
              self.bank_account_id.default_credit_account_id.id])]
        ).mapped(field)
        if move_line:
            return sum(move_line)
        return False

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        Result = self.env['account.move.line']
        dom = [('journal_id', '=', self.bank_account_id.id),
               ('account_id', 'in',
               [self.bank_account_id.default_debit_account_id.id,
                self.bank_account_id.default_credit_account_id.id]),
               ('date_maturity', '>=', self.date_from),
               ('date_maturity', '<=', self.date_to)]
        self.results = Result.search(dom, order='date_maturity, name')


class BankStatementReportCompute(models.TransientModel):
    _inherit = 'report.bank.statement'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'bank_statement_xlsx'
        else:
            report_name = 'l10n_th_bank_statement_report.' \
                          'report_bank_statement_qweb'

        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)],
            limit=1).report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'l10n_th_bank_statement_report.report_bank_statement').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()
