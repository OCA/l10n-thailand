# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    tax_date = fields.Date()
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
    show_cancel = fields.Boolean(string="Show Cancelled")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="tax.report.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _query_select_tax(self):
        return """company_id, account_id, partner_id, tax_invoice_number,
            tax_date, name, sum(tax_base_amount) tax_base_amount,
            sum(tax_amount) tax_amount"""

    def _query_select_sub_tax(self):
        return """t.id, t.company_id, ml.account_id, t.partner_id,
            case when ml.parent_state = 'posted' and t.reversing_id is null
            then t.tax_invoice_number else
            t.tax_invoice_number || ' (VOID)' end as tax_invoice_number,
            t.tax_invoice_date as tax_date,
            case when ml.parent_state = 'posted' and t.reversing_id is null
            then t.tax_base_amount else 0.0 end as tax_base_amount,
            case when ml.parent_state = 'posted' and t.reversing_id is null
            then t.balance else 0.0 end as tax_amount,
            case when m.ref is not null
            then m.ref else ml.move_name end as name"""

    def _query_groupby_tax(self):
        return "company_id, account_id, partner_id, tax_invoice_number, tax_date, name"

    def _domain_where_clause_tax(self):
        reverse_cancel = ""
        if self.show_cancel:
            condition = "in ('posted', 'cancel')"
        else:
            condition = "= 'posted'"
            reverse_cancel = "and t.reversing_id is null"
        return " ".join(["ml.parent_state", condition, reverse_cancel])

    def _compute_results(self):
        self.ensure_one()
        domain = self._domain_where_clause_tax()
        self._cr.execute(
            """
            select {}
            from (
                select {}
                from account_move_tax_invoice t
                join account_move_line ml on ml.id = t.move_line_id
                join account_move m on m.id = ml.move_id
                where {}
                and t.tax_invoice_number is not null
                and ml.account_id in (select distinct account_id
                                        from account_tax_repartition_line
                                        where account_id is not null
                                        and invoice_tax_id = %s or refund_tax_id = %s)
                -- query condition with normal report date by report date
                -- and late report date within range date end
                and (
                    (t.report_date >= %s and t.report_date <= %s)
                    or (
                        t.report_late_mo != '0' and
                        EXTRACT(MONTH FROM t.report_date) <= %s and
                        EXTRACT(YEAR FROM t.report_date) <= %s and
                        EXTRACT(MONTH FROM t.report_date) >= %s and
                        EXTRACT(YEAR FROM t.report_date) >= %s
                    )
                )
                and ml.company_id = %s
                and t.reversed_id is null
            ) a
            group by {}
            order by tax_date, tax_invoice_number
        """.format(
                self._query_select_tax(),
                self._query_select_sub_tax(),
                domain,
                self._query_groupby_tax(),
            ),
            (
                self.tax_id.id,
                self.tax_id.id,
                self.date_from,
                self.date_to,
                self.date_to.month,
                self.date_to.year,
                self.date_from.month,
                self.date_from.year,
                self.company_id.id,
            ),
        )
        tax_report_results = self._cr.dictfetchall()
        ReportLine = self.env["tax.report.view"]
        self.results = False
        for line in tax_report_results:
            self.results += ReportLine.new(line)

    def print_report(self, report_type="qweb-pdf"):
        self.ensure_one()
        action = False
        if report_type == "xlsx":
            action = self.env.ref("l10n_th_account_tax_report.action_tax_report_xlsx")
        elif report_type == "qweb-pdf":
            if self.company_id.tax_report_format == "rd":
                action = self.env.ref(
                    "l10n_th_account_tax_report.action_rd_tax_report_pdf"
                )
            else:
                action = self.env.ref(
                    "l10n_th_account_tax_report.action_tax_report_pdf"
                )
        if not action:
            raise ValidationError(_("Invalid Reporting Data!"))
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "l10n_th_account_tax_report.report_tax_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**given_context)._get_html()

    def _get_period_be(self, date_start, date_end):
        month = year = "-"
        date_start = (date_start + relativedelta(years=543)).strftime("%m-%Y")
        date_end = (date_end + relativedelta(years=543)).strftime("%m-%Y")
        if date_start == date_end:
            m, year = date_end.split("-")
            month = self._get_month_thai(m)
        return [month, year]

    def _get_month_thai(self, month):
        month_thai = {
            "01": "มกราคม",
            "02": "กุมภาพันธ์",
            "03": "มีนาคม",
            "04": "เมษายน",
            "05": "พฤษภาคม",
            "06": "มิถุนายน",
            "07": "กรกฎาคม",
            "08": "สิงหาคม",
            "09": "กันยายน",
            "10": "ตุลาคม",
            "11": "พฤศจิกายน",
            "12": "ธันวาคม",
        }
        return month_thai[month]
