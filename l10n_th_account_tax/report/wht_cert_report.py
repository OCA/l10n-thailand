# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models
from odoo.tools import misc


class ReportWhtCert(models.AbstractModel):
    _name = "report.l10n_th_account_tax.report_wht_cert"
    _description = "Withholding Tax Certificate Report (50 Tawi)"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            "doc_ids": docids,
            "doc_model": "withholding.tax.cert",
            "docs": self.env["withholding.tax.cert"].browse(docids),
            # As the standard 50 Tawi report, in Thai if enabled
            "report_lang": misc.get_lang(self.env, "th_TH").code,
            "data": data,
        }
