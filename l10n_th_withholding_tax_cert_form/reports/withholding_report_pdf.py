# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ReportWithholdingTaxCert(models.AbstractModel):
    _name = "report.withholding_tax_pdf"
    _description = "Withholding tax cert report with pdf preprint"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "withholding_tax_pdf"
        )
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "docs": self.env[report.model].browse(docids),
            "report_type": data.get("report_type") if data else "",
        }
