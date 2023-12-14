# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TaxReportView(models.TransientModel):
    _inherit = "tax.report.view"

    operating_unit_id = fields.Many2one(comodel_name="operating.unit")


class TaxReport(models.TransientModel):
    _inherit = "report.tax.report"

    operating_unit_ids = fields.Many2many(comodel_name="operating.unit")
    show_operating_unit = fields.Boolean()

    def _query_select_tax(self):
        query_select = super()._query_select_tax()
        query_select += ", operating_unit_id"
        return query_select

    def _query_select_sub_tax(self):
        query_select_sub_tax = super()._query_select_sub_tax()
        query_select_sub_tax += ", t.operating_unit_id"
        return query_select_sub_tax

    def _query_groupby_tax(self):
        query_groupby = super()._query_groupby_tax()
        query_groupby += ", operating_unit_id"
        return query_groupby

    def _domain_where_clause_tax(self):
        domain = super()._domain_where_clause_tax()
        if not self.operating_unit_ids:
            return domain
        if len(self.operating_unit_ids) > 1:
            condition = "in {}".format(tuple(self.operating_unit_ids.ids))
        else:
            condition = "= {}".format(self.operating_unit_ids.id)
        domain_ou = " ".join([domain, "and t.operating_unit_id", condition])
        return domain_ou
