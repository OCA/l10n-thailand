# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TaxReportView(models.TransientModel):
    _inherit = "tax.report.view"

    company_tax_branch = fields.Many2one(comodel_name="res.branch")


class TaxReport(models.TransientModel):
    _inherit = "report.tax.report"

    branch_ids = fields.Many2many(comodel_name="res.branch")

    def _query_select_tax(self):
        query_select = super()._query_select_tax()
        query_select += ", company_tax_branch"
        return query_select

    def _query_select_sub_tax(self):
        query_select_sub_tax = super()._query_select_sub_tax()
        query_select_sub_tax += ", t.branch_id as company_tax_branch"
        return query_select_sub_tax

    def _query_groupby_tax(self):
        query_groupby = super()._query_groupby_tax()
        query_groupby += ", company_tax_branch"
        return query_groupby

    def _domain_where_clause_tax(self):
        domain = super()._domain_where_clause_tax()
        if not self.branch_ids:
            return domain
        if len(self.branch_ids) > 1:
            condition = "in {}".format(tuple(self.branch_ids.ids))
        else:
            condition = "= {}".format(self.branch_ids.id)
        domain_tax_branch = " ".join([domain, "and t.branch_id", condition])
        return domain_tax_branch

    def _get_tax_branch_filter(self, tax_branch=False):
        if not tax_branch:
            tax_branch = self.env["res.branch"].search(
                [("company_id", "=", self.company_id.id)]
            )
        return ", ".join(tax_branch.mapped("name"))
