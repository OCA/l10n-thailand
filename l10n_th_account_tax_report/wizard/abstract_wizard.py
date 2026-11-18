# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountTaxReportAbstractWizard(models.AbstractModel):
    _name = "account.tax.report.abstract.wizard"
    _inherit = "thai.utils"
    _description = "Abstract Wizard"

    date_range_id = fields.Many2one(comodel_name="date.range")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    show_cancel = fields.Boolean(
        string="Show Cancelled",
        default=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company.id,
        required=False,
        string="Company",
    )

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(self.env._("Date From must not be after Date To"))

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
        self.ensure_one()
        # Implement in _get_report_name()
        report_name, data = self._get_report_name(report_type)

        report = self.env["ir.actions.report"].search(
            [("report_name", "=", report_name), ("report_type", "=", report_type)],
            limit=1,
        )
        report_action = report.report_action(self, data=data, config=False)

        # NOTE:
        # Normally, when downloading a PDF report from a wizard,
        # the system uses the default `report_name` (defined in ir.actions.report).
        # If we want the PDF filename to follow the `print_report_name` logic,
        # Odoo requires a record-specific identifier (e.g., record ID) in `report_name`.
        #
        # Example:
        #   Default: sale.report_saleorder --> "Quotation.pdf"
        #   With ID: sale.report_saleorder/42 --> "Quotation - S00001.pdf"
        #
        # In this case, we append `self.id` to the report_name
        # so the generated filename can be customized properly.
        report_action["report_name"] = f"{report_action['report_name']}/{self.id}"
        return report_action
