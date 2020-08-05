# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models

DEFAULT_DAY_FORMAT_WHT = "%d"
DEFAULT_MONTH_FORMAT_WHT = "%m"
DEFAULT_YEAR_FORMAT_WHT = "%Y"
INCOME_TAX_FORM = {"pnd3": "P03", "pnd53": "P53"}


class WithHoldingTaxReport(models.TransientModel):
    _name = "withholding.tax.report"
    _description = "Withholding Tax Report"

    income_tax_form = fields.Selection(
        selection=[("pnd3", "PND3"), ("pnd53", "PND53")],
        string="Income Tax Form",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", required=True, ondelete="cascade",
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

    def _create_text(self, docs):
        self.ensure_one()
        for obj in docs:
            text = ""
            for idx, line in enumerate(obj.results):
                text += "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                    idx + 1,
                    line.cert_id.supplier_partner_id.vat or "",
                    "",  # Title name
                    line.cert_id.supplier_partner_id.display_name or "",
                    line.cert_id.supplier_partner_id._display_address(
                        without_company=True
                    )
                    or "",
                    self.format_date_dmy(line.cert_id.date),
                    "ค่าบริการ",  # line.wt_cert_income_desc or "",
                    "{:,.2f}".format(line.wt_percent / 100) or 0.00,
                    "{:,.2f}".format(line.base) or 0.00,
                    "{:,.2f}".format(line.amount) or 0.00,
                    self._convert_tax_payer(line.cert_id.tax_payer),
                )
        return text

    def _convert_tax_payer(self, tax_payer):
        if tax_payer == "withholding":
            return 1
        return 2

    def format_date_dmy(self, date=None):
        if not date:
            date = fields.Date.context_today()
        year_thai = int(date.strftime(DEFAULT_YEAR_FORMAT_WHT)) + 543
        date_format = date.strftime(
            "{}/{}/{}".format(
                DEFAULT_DAY_FORMAT_WHT, DEFAULT_MONTH_FORMAT_WHT, year_thai
            )
        )
        return date_format

    def format_date(self, date=None):
        if not date:
            # date month before
            date = self.date_from
        year_thai = int(date.strftime(DEFAULT_YEAR_FORMAT_WHT)) + 543
        month = date.strftime(DEFAULT_MONTH_FORMAT_WHT)
        date_format = "{}{}".format(year_thai, month)
        return date_format

    def format_pnd(self, pnd):
        pnd = INCOME_TAX_FORM[pnd]
        return pnd

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        if report_type == "xlsx":
            report_name = "withholding.tax.report.xlsx"
        elif report_type == "qweb-text":
            report_name = "l10n_th_withholding_tax_report.report_withholding_tax_text"
        else:
            report_name = "l10n_th_withholding_tax_report.report_withholding_tax_qweb"
        context = dict(self._context)
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
        if self.company_id:
            domain += [
                ("cert_id.company_partner_id", "=", self.company_id.partner_id.id)
            ]
        self.results = Result.search(domain)
