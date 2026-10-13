# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class RDThaiTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_rd_thai_tax"
    _inherit = "report.l10n_th_account_tax_report.report_thai_tax"
    _description = "Thai Tax Report RD"

    def _get_report_values(self, docids, data):
        report_values = super()._get_report_values(docids, data)

        data = report_values["docs"]._prepare_report_tax()

        company = self.env["res.company"].browse(data["company_id"])
        report_values["company_address"] = company.partner_id._display_address(
            without_company=True
        )
        return report_values
