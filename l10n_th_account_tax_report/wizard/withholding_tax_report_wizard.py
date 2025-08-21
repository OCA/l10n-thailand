# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

INCOME_TAX_FORM = {
    "pnd1": "P01",
    "pnd1a": "P01A",
    "pnd2": "P02",
    "pnd3": "P03",
    "pnd53": "P53",
}


class WithHoldingTaxReportWizard(models.TransientModel):
    _name = "withholding.tax.report.wizard"
    _inherit = "account.tax.report.abstract.wizard"
    _description = "Withholding Tax Report Wizard"

    income_tax_form = fields.Selection(
        selection=[
            ("pnd1", "PND1"),
            ("pnd1a", "PND1A"),
            ("pnd2", "PND2"),
            ("pnd3", "PND3"),
            ("pnd53", "PND53"),
        ],
        required=True,
    )

    def _get_report_base_filename(self):
        self.ensure_one()
        pnd = INCOME_TAX_FORM[self.income_tax_form]
        date_format = self.format_thai_date(
            self.date_from, month_format="numeric", format_date="{year}{month}"
        )
        return f"WHT-{pnd}-{date_format}"

    def _prepare_report_wht(self):
        self.ensure_one()
        return {
            "wizard_id": self.id,
            "company_id": self.company_id.id,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "income_tax_form": self.income_tax_form,
            "show_cancel": self.show_cancel,
        }

    def button_export_txt(self):
        self.ensure_one()
        report_type = "qweb-text"
        return self._export(report_type)

    def _get_report_name(self, report_type):
        self.ensure_one()
        data = self._prepare_report_wht()
        if report_type == "xlsx":
            report_name = "l10n_th_account_tax_report.report_withholding_tax_xlsx"
        elif report_type == "qweb-text":
            report_name = "l10n_th_account_tax_report.report_withholding_tax_text"
        else:
            if self.company_id.wht_report_format == "rd" and report_type == "qweb-pdf":
                report_name = "l10n_th_account_tax_report.report_rd_withholding_tax"
            else:
                report_name = "l10n_th_account_tax_report.report_withholding_tax"
        return report_name, data
