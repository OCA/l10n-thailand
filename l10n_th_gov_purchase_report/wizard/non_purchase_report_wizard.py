# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class NonPurchaseReportWizard(models.TransientModel):
    _name = "non.purchase.report.wizard"
    _inherit = "common.purchase.wizard"
    _description = "Non Purchase Report Wizard"

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="hr.expense",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        dom = [
            ("purchase_type_id", "!=", False),
            ("sheet_id.state", "in", ["post", "done"]),
        ]
        # Filter report by accounting date
        if self.date_from:
            dom += [("accounting_date", ">=", self.date_from)]
        if self.date_to:
            dom += [("accounting_date", "<=", self.date_to)]
        self.results = self.env["hr.expense"].search(dom, order="date")

    def _get_report_name(self):
        return "l10n_th_gov_purchase_report.report_non_purchase_xlsx"
