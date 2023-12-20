# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # For case print from html, it will change report withholding tax to RD Format
        if (
            self._get_report(report_ref).report_name
            == "l10n_th_account_tax_report.report_withholding_tax"
            and self.env.company.wht_report_format == "rd"
        ):
            report_ref = "l10n_th_account_tax_report.report_rd_withholding_tax"
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
