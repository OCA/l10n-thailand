# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseReportWizard(models.TransientModel):
    _name = "purchase.report.wizard"
    _inherit = "common.purchase.wizard"
    _description = "Purchase Report Wizard"

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="purchase.report.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        procurement_report_results = self._get_query_purchase_report()
        ReportLine = self.env["purchase.report.view"]
        self.results = False
        previous_id = False
        for line in procurement_report_results:
            # skip it if line duplicate
            if previous_id == line["requisition_id"]:
                continue
            previous_id = line["requisition_id"]
            self.results += ReportLine.new(line)

    def _get_where_purchase_report(self):
        where_domain = (
            "WHERE company_id = {} and date_signed >= '{}' "
            "and date_signed <= '{}'".format(
                self.company_id.id, self.date_from, self.date_to
            )
        )
        return where_domain

    def _get_query_purchase_report(self):
        self._cr.execute(
            """
            SELECT *
            FROM (
                SELECT
                    pa.id AS requisition_id, pa.company_id, po.id as purchase_order_id,
                    CASE
                        WHEN bool(agm.id) THEN agm.signature_date
                        ELSE po.date_approve
                    END as date_signed,
                    agm.code as agreement_name,
                    po.name as po_name,
                    STRING_AGG(DISTINCT pr.description, ',') AS description,
                    SUM(DISTINCT pr.estimated_cost) AS pr_amount,
                    STRING_AGG(DISTINCT pm.name, ',') AS procurement_method
                FROM purchase_requisition pa
                LEFT JOIN purchase_requisition_line pa_line
                    ON pa.id = pa_line.requisition_id
                LEFT JOIN purchase_request_purchase_requisition_line_rel pr_pa_line
                    ON pa_line.id = pr_pa_line.purchase_requisition_line_id
                LEFT JOIN purchase_request_line pr_line
                    ON pr_pa_line.purchase_request_line_id = pr_line.id
                LEFT JOIN purchase_request pr
                    ON pr_line.request_id = pr.id
                LEFT JOIN procurement_method pm
                    ON pr.procurement_method_id = pm.id
                LEFT JOIN purchase_order po on pa.id  = po.requisition_id
                LEFT JOIN agreement agm on agm.purchase_order_id = po.id
                WHERE po.state in ('purchase', 'done')
                GROUP BY pa.id, po.id, agm.id
                ORDER BY pa.id, agm.id desc
            ) report {}
            """.format(
                self._get_where_purchase_report()
            )
        )
        return self.env.cr.dictfetchall()

    def _get_report_name(self):
        return "l10n_th_gov_purchase_report.report_purchase_xlsx"


class PurchaseReportView(models.TransientModel):
    _name = "purchase.report.view"
    _description = "Purchase Report View"
    _order = "id"

    requisition_id = fields.Many2one(
        comodel_name="purchase.requisition", string="Purchase Agreement", index=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", index=True
    )
    purchase_order_id = fields.Many2one(comodel_name="purchase.order")
    date_signed = fields.Date(string="Signed Date")
    agreement_name = fields.Char()
    po_name = fields.Char()
    description = fields.Char(string="Objective")
    pr_amount = fields.Float()
    procurement_method = fields.Char()
    # market_price = fields.Float(string="Market Price")
