# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class RDWithholdingTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_rd_withholding_tax"
    _inherit = "report.l10n_th_account_tax_report.report_withholding_tax"
    _description = "Thai Withholding Tax Report RD"
