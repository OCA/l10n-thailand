# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WithHoldingTaxReport(models.TransientModel):
    _name = "withholding.tax.report"
    _description = "Withholding Tax Report"

    income_tax_form = fields.Selection(
        selection=[("pnd3", "PND3"), ("pnd53", "PND53")],
        string="Income Tax Form",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        string="Company",
        required=True,
        ondelete="cascade",
    )
    date_range_id = fields.Many2one(
        comodel_name="date.range", string="Date range", required=True
    )
    date_from = fields.Date()
    date_to = fields.Date()
    results = fields.Many2many(
        comodel_name="withholding.tax.cert.line",
        string="Results",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        if report_type == "xlsx":
            report_name = "withholding.tax.report.xlsx"
        elif report_type == "csv":
            report_name = "report_withholding_tax_csv"
        else:
            report_name = "l10n_th_withholding_tax_report.report_withholding_tax_qweb"
        context = dict(self.env.context)
        action = self.env["ir.actions.report"].search(
            [("report_name", "=", report_name), ("report_type", "=", report_type)],
            limit=1,
        )
        return action.with_context(context).report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "l10n_th_withholding_tax_report.report_withholding_tax_html"
            ).render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    def _compute_results(self):
        self.ensure_one()
        Result = self.env["withholding.tax.cert.line"]
        domain = []
        if self.income_tax_form:
            domain += [("cert_id.income_tax_form", "=", self.income_tax_form)]
        if self.date_from:
            domain += [("cert_id.date", ">=", self.date_from)]
        if self.date_to:
            domain += [("cert_id.date", "<=", self.date_to)]
        self.results = Result.search(domain)
