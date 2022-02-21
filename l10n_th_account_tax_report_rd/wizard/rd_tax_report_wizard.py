# Copyright 2022 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RdTaxReportWizard(models.TransientModel):
    _name = "rd.tax.report.wizard"
    _description = "Wizard for Tax RD Report"

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
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _prepare_tax_report(self):
        self.ensure_one()
        return {
            "company_id": self.company_id.id,
            "tax_id": self.tax_id.id,
            "date_range_id": self.date_range_id and self.date_range_id.id or False,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }

    def _export(self, report_type):
        model = self.env["report.rd.tax.report"]
        report = model.create(self._prepare_tax_report())
        return report.print_report(report_type)

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end
