# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

TAX_REPORT_WIZARDS = ("tax.report.wizard", "withholding.tax.report.wizard")


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Print button of the HTML view prints the report of the view, e.g. the
        standard WHT report even with the RD format, that is not shown in HTML.
        Print the PDF report of the wizard instead, as with Export PDF."""
        report = self._get_report(report_ref)
        if report.model in TAX_REPORT_WIZARDS and res_ids:
            wizard = self.env[report.model].browse(res_ids)
            if len(wizard) == 1:
                report_ref = wizard._get_report_name("qweb-pdf")[0]
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
