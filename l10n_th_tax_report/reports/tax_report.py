# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class TaxReportView(models.TransientModel):
    _name = "tax.report.view"
    _description = "Tax Report View"
    _inherit = "account.move.line"
    _order = "id"

    tax_base_amount = fields.Float()
    tax_amount = fields.Float()
    tax_date = fields.Char()
    tax_invoice_number = fields.Char()


class TaxReport(models.TransientModel):
    _name = "report.tax.report"
    _description = "Report Tax Report"

    # Filters fields, used for data computation
    company_id = fields.Many2one(comodel_name="res.company")
    tax_id = fields.Many2one(comodel_name="account.tax")
    account_id = fields.Many2one(comodel_name="account.account")
    date_range_id = fields.Many2one(comodel_name="date.range")
    date_from = fields.Date()
    date_to = fields.Date()

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="tax.report.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        self._cr.execute(
            """
            select aml.id as id, am.company_id, am.name, aml.account_id,
                amti.tax_invoice_number, aml.partner_id, aml.date as tax_date,
                case when am.type in ('out_invoice', 'in_invoice')
                then aml.tax_base_amount
                else aml.tax_base_amount end as tax_base_amount,
                case when aa.internal_group = 'asset'
                then aml.balance
                else -aml.balance end as tax_amount
            from account_move_line aml
            left join account_move am on aml.move_id = am.id
            join account_account aa on aa.id = aml.account_id
            join account_move_tax_invoice amti on aml.tax_invoice_id = amti.id
            where aml.tax_line_id is not null and aml.date >= %s and
                aml.date <= %s and aml.company_id = %s and
                aml.account_id = %s and am.invoice_payment_state = 'paid'
            order by amti.tax_invoice_date, am.name
        """,
            (self.date_from, self.date_to, self.company_id.id, self.account_id.id),
        )
        tax_report_results = self._cr.dictfetchall()
        ReportLine = self.env["tax.report.view"]
        self.results = False
        for line in tax_report_results:
            self.results += ReportLine.new(line)

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("l10n_th_tax_report.action_tax_report_xlsx")
            or self.env.ref("l10n_th_tax_report.action_tax_report_pdf")
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "l10n_th_tax_report.report_tax_report_html"
            ).render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
