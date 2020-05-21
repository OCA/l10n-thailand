# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class TaxReportView(models.TransientModel):
    _name = "tax.report.view"
    _description = "Tax Report View"
    _order = "id"

    name = fields.Char()
    company_id = fields.Many2one("res.company")
    account_id = fields.Many2one("account.account")
    partner_id = fields.Many2one("res.partner")
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
            select company_id, account_id, partner_id,
                tax_invoice_number, tax_date, name,
                sum(tax_base_amount) tax_base_amount, sum(tax_amount) tax_amount
            from (
            select t.id, t.company_id, ml.account_id, ml.partner_id,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.tax_invoice_number else
                t.tax_invoice_number || ' (VOID)' end as tax_invoice_number,
              t.tax_invoice_date as tax_date,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.tax_base_amount else 0.0 end as tax_base_amount,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.balance else 0.0 end as tax_amount,
              case when p.communication is not null
                then p.communication else ml.move_name end as name
            from account_move_tax_invoice t
              join account_move_line ml on ml.id = t.move_line_id
              left outer join account_payment p on p.id = t.payment_id
            where ml.parent_state in ('posted', 'cancel')
              and t.tax_invoice_number is not null
              and ml.account_id in (select distinct account_id
                                    from account_tax_repartition_line
                                    where account_id is not null
                                    and invoice_tax_id = %s or refund_tax_id = %s)
              and ml.date >= %s and ml.date <= %s
              and ml.company_id = %s
              and t.reversed_id is null
            ) a
            group by company_id, account_id, partner_id,
                tax_invoice_number, tax_date, name
            order by tax_date, tax_invoice_number
        """,
            (
                self.tax_id.id,
                self.tax_id.id,
                self.date_from,
                self.date_to,
                self.company_id.id,
            ),
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
