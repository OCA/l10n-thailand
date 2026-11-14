# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError

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
    can_export_txt = fields.Boolean(compute="_compute_can_export_txt")

    @api.depends("income_tax_form")
    def _compute_can_export_txt(self):
        for wizard in self:
            field = wizard._get_textfile_format_field()
            wizard.can_export_txt = field in self.env["res.company"]._fields

    def _get_textfile_format_field(self):
        """Field of the company with the text file format of the form"""
        return f"wht_text_file_{self.income_tax_form}_format"

    def _get_textfile_format(self):
        self.ensure_one()
        form = dict(self._fields["income_tax_form"].selection)[self.income_tax_form]
        if not self.can_export_txt:
            raise UserError(
                self.env._("Text file export is not available for %s.", form)
            )
        textfile_format = self.company_id[self._get_textfile_format_field()]
        if not textfile_format:
            raise UserError(
                self.env._("Set the text file format of %s in the settings.", form)
            )
        return textfile_format

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
        self._get_textfile_format()
        return self._export("qweb-text")

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
