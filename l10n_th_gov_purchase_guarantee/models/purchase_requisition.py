# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    purchase_guarantee_ids = fields.One2many(
        comodel_name="purchase.guarantee",
        inverse_name="requisition_id",
        string="Guarantee",
    )
    purchase_guarantee_count = fields.Integer(
        string="Guarantee Count",
        compute="_compute_purchase_guarantee_count",
    )

    @api.depends("purchase_guarantee_ids")
    def _compute_purchase_guarantee_count(self):
        for rec in self:
            rec.purchase_guarantee_count = len(rec.purchase_guarantee_ids)

    def action_view_purchase_guarantee(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_th_gov_purchase_guarantee.purchase_guarantee_action"
        )
        result["domain"] = [("requisition_id", "=", self.id)]
        result["context"] = {
            "default_reference": f"purchase.requisition,{self.id}",
        }
        return result


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic Tags",
    )
