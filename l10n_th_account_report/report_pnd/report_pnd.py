from odoo import models, fields, api


class ReportPND(models.TransientModel):
    _name = 'report.pnd'
    _description = 'Wizard for report.pnd'
    _inherit = 'xlsx.report'

    # Search Criteria
    income_tax_form = fields.Selection(
        [('pnd3', 'PND3'),
         ('pnd53', 'PND53')],
        string='Income Tax Form',
        required=True,
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range',
        required=True,
    )
    date_from = fields.Date(
        string='Date From',
    )
    date_to = fields.Date(
        string='Date To',
    )
    # Report Result, withholding.tax.cert.line
    results = fields.Many2many(
        'withholding.tax.cert.line',
        string='Results',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        Result = self.env['withholding.tax.cert.line']
        domain = []
        if self.income_tax_form:
            domain += [('cert_id.income_tax_form', '=', self.income_tax_form)]
        if self.date_from:
            domain += [('cert_id.date', '>=', self.date_from)]
        if self.date_to:
            domain += [('cert_id.date', '<=', self.date_to)]
        self.results = Result.search(domain)
