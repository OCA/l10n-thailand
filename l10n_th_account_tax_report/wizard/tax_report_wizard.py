# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import fields, models


class TaxReportWizard(models.TransientModel):
    _name = "tax.report.wizard"
    _inherit = "account.tax.report.abstract.wizard"
    _description = "Wizard for Tax Report"

    # Search Criteria
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

    def _get_report_base_filename(self):
        self.ensure_one()
        date_format = self.format_thai_date(
            self.date_from, month_format="numeric", format_date="{year}{month}"
        )
        return f"{self.tax_id.display_name}-{date_format}"

    def _get_period_be(self, date_start, date_end):
        month = year = "-"
        if date_start.strftime("%m-%Y") == date_end.strftime("%m-%Y"):
            month = self.thai_month_name(date_end.month)
            year = self.format_thai_date(date_end, format_date="{year}")
        return [month, year]

    def _prepare_report_tax(self):
        self.ensure_one()
        return {
            "wizard_id": self.id,
            "company_id": self.company_id.id,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "tax_id": self.tax_id.id,
            "show_cancel": self.show_cancel,
        }

    def _get_report_name(self, report_type):
        self.ensure_one()
        data = self._prepare_report_tax()
        if report_type == "xlsx":
            report_name = "l10n_th_account_tax_report.report_thai_tax_xlsx"
        else:
            if self.company_id.tax_report_format == "rd":
                report_name = "l10n_th_account_tax_report.report_rd_thai_tax"
            else:
                report_name = "l10n_th_account_tax_report.report_thai_tax"
        return report_name, data
