# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TaxReportWizard(models.TransientModel):
    _name = "tax.report.wizard"
    _description = "Wizard for Tax Report"

    # Search Criteria
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        string="Company",
        required=True,
        ondelete="cascade",
    )
    tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Tax",
        required=True,
        domain=[
            ("tax_exigibility", "=", "on_invoice"),
            ("type_tax_use", "in", ["sale", "purchase"]),
            ("include_base_amount", "=", False),
        ],
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Period")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    show_cancel = fields.Boolean(
        string="Show Cancelled",
        default=True,
    )

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="tax.report.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_("Date From must not be after Date To"))

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)

    def _print_report(self, report_type):
        self.ensure_one()
        if report_type == "xlsx":
            report_name = "l10n_th_account_tax_report.report_thai_tax_xlsx"
        else:
            if self.company_id.tax_report_format == "rd":
                report_name = "l10n_th_account_tax_report.report_rd_thai_tax"
            else:
                report_name = "l10n_th_account_tax_report.report_thai_tax"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, config=False)
        )

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    def format_date_ym_wht(self, date=None):
        date = date or self.date_from
        year_thai = date.year + 543
        date_format = f"{year_thai}{str(date.month).zfill(2)}"
        return date_format

    def format_tax_date(self, date, format_date=None):
        """
        Format a given date to a custom string format with support
        for Thai Buddhist year.

        This function returns a formatted date string based on the given `format_date`.
        - It supports 3 format placeholders: `{day}`, `{month}`, and `{year}`.
        - `{day}`   = two-digit day (e.g. 01)
        - `{month}` = two-digit month (e.g. 12)
        - `{year}`  = year in Thai Buddhist calendar (e.g. 2567)

        Parameters:
            date (datetime.date): The date to format.
            format_date (str, optional): A format string using the placeholders.
                Example: "{day}/{month}/{year}" → "01/01/2567"

        Returns:
            str: Formatted date string.

        If `format_date` is not provided,
        the default format is "ddmmyyyy" (e.g. "01012567").

        Example usage:
            format_tax_date(date(2024, 1, 1), "{day}/{month}/{year}")
            → "01/01/2567"
        """
        if format_date is None:
            format_date = "{day}{month}{year}"
        year_thai = date.year + 543
        date_format = format_date.format(
            day=str(date.day).zfill(2), month=str(date.month).zfill(2), year=year_thai
        )
        return date_format

    def _get_report_base_filename(self):
        self.ensure_one()
        date_format = self.format_date_ym_wht()
        return f"{self.tax_id.display_name}-{date_format}"

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

    def _query_select_tax(self):
        return """company_id, account_id, partner_id, tax_invoice_number,
            tax_date, name, sum(tax_base_amount) tax_base_amount,
            sum(tax_amount) tax_amount"""

    def _query_select_sub_tax(self):
        return """t.id, t.company_id, ml.account_id, t.partner_id,
            CASE WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                THEN t.tax_invoice_number
            ELSE
                t.tax_invoice_number || ' (VOID)'
            END AS tax_invoice_number,
            t.tax_invoice_date AS tax_date,
            CASE WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                THEN t.tax_base_amount
            ELSE 0.0
            END AS tax_base_amount,
            CASE WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                THEN t.balance
            ELSE 0.0
            END AS tax_amount,
            CASE WHEN m.ref IS NOT NULL
                THEN m.ref
            ELSE ml.move_name
            END AS name
        """

    def _query_groupby_tax(self):
        return "company_id, account_id, partner_id, tax_invoice_number, tax_date, name"

    def _domain_where_clause_tax(self):
        reverse_cancel = ""
        if self.show_cancel:
            condition = "IN ('posted', 'cancel')"
        else:
            condition = "= 'posted'"
            reverse_cancel = "AND t.reversing_id IS NULL"
        return " ".join(["ml.parent_state", condition, reverse_cancel])

    def _compute_results(self):
        self.ensure_one()
        domain = self._domain_where_clause_tax()
        self._cr.execute(
            f"""
            SELECT {self._query_select_tax()}
            FROM (
                SELECT {self._query_select_sub_tax()}
                FROM account_move_tax_invoice t
                JOIN account_move_line ml ON ml.id = t.move_line_id
                JOIN account_move m ON m.id = ml.move_id
                WHERE {domain}
                    AND t.tax_invoice_number IS NOT NULL
                    AND ml.account_id IN (
                        SELECT distinct account_id
                        FROM account_tax_repartition_line
                        WHERE account_id is not null
                            AND tax_id = %s)
                    -- query condition with normal report date by report date
                    -- and late report date within range date end
                    AND (
                        (t.report_date >= %s AND t.report_date <= %s)
                        OR (
                            t.report_late_mo != '0' AND
                            EXTRACT(MONTH FROM t.report_date) <= %s AND
                            EXTRACT(YEAR FROM t.report_date) <= %s AND
                            EXTRACT(MONTH FROM t.report_date) >= %s AND
                            EXTRACT(YEAR FROM t.report_date) >= %s
                        )
                    )
                AND ml.company_id = %s
                AND t.reversed_id is null
            ) a
            GROUP BY {self._query_groupby_tax()}
            ORDER BY tax_date, tax_invoice_number
        """,
            (
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


class TaxReportView(models.TransientModel):
    _name = "tax.report.view"
    _description = "Tax Report View"
    _order = "id"

    name = fields.Char()
    company_id = fields.Many2one(comodel_name="res.company")
    account_id = fields.Many2one(comodel_name="account.account")
    partner_id = fields.Many2one(comodel_name="res.partner")
    tax_base_amount = fields.Float()
    tax_amount = fields.Float()
    tax_date = fields.Date()
    tax_invoice_number = fields.Char()
