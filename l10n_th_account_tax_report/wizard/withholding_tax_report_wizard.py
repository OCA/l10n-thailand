# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WithHoldingTaxReportWizard(models.TransientModel):
    _name = "withholding.tax.report.wizard"
    _description = "Withholding Tax Report Wizard"

    income_tax_form = fields.Selection(
        selection=[
            ("pnd1", "PND1"),
            ("pnd1a", "PND1A"),
            ("pnd3", "PND3"),
            ("pnd53", "PND53"),
        ],
        required=True,
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date Range")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        domain=lambda self: self._get_domain_company_id(),
        string="Company",
        required=True,
        ondelete="cascade",
    )
    show_cancel = fields.Boolean(
        string="Show Cancelled",
        default=True,
    )

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_("Date From must not be after Date To"))

    def _get_domain_company_id(self):
        selected_companies = self.env["res.company"].browse(
            self.env.context.get("allowed_company_ids")
        )
        return [("id", "in", selected_companies.ids)]

    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            "l10n_th_account_tax_report.action_report_tax_report_html"
        )
        vals = action.sudo().read()[0]
        context1 = {"active_model": "withholding.tax.report"}
        model = self.env["withholding.tax.report"]
        report = model.create(self._prepare_wht_report())
        context1["active_id"] = report.id
        context1["active_ids"] = report.ids
        vals["context"] = context1
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def button_export_txt(self):
        self.ensure_one()
        report_type = "qweb-text"
        return self._export(report_type)

    def _prepare_wht_report(self):
        self.ensure_one()
        return {
            "income_tax_form": self.income_tax_form,
            "date_range_id": self.date_range_id and self.date_range_id.id or False,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "company_id": self.company_id.id,
            "show_cancel": self.show_cancel,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env["withholding.tax.report"]
        report = model.create(self._prepare_wht_report())
        return report.print_report(report_type)

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end
