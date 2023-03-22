# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CommonPurchaseWizard(models.AbstractModel):
    _name = "common.purchase.wizard"
    _description = "Common Purchase Report Wizard"

    date_range_id = fields.Many2one(
        comodel_name="date.range",
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )

    @api.onchange("date_range_id")
    def _onchange_date_range(self):
        for rec in self:
            if rec.date_range_id:
                rec.date_from = rec.date_range_id.date_start
                rec.date_to = rec.date_range_id.date_end

    def _get_report_name(self):
        """Hook this function for get report name"""
        return False

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._print_report(report_type)

    def _print_report(self, report_type):
        self.ensure_one()
        if report_type == "xlsx":
            report_name = self._get_report_name()
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, config=False)
        )
