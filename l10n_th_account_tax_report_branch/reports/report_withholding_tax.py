# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class WithHoldingTaxReport(models.TransientModel):
    _inherit = "withholding.tax.report"

    branch_ids = fields.Many2many(comodel_name="res.branch")

    def _get_domain_wht(self):
        domain = super()._get_domain_wht()
        if not self.branch_ids:
            return domain
        if len(self.branch_ids) > 1:
            domain.append(("cert_id.branch_id", "in", self.branch_ids.ids))
        else:
            domain.append(("cert_id.branch_id", "=", self.branch_ids.id))
        return domain

    def _get_tax_branch_filter(self, tax_branch=False):
        if not tax_branch:
            tax_branch = self.env["res.branch"].search(
                [("company_id", "=", self.company_id.id)]
            )
        return ", ".join(tax_branch.mapped("name"))
