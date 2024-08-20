# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    agreement_ids = fields.One2many(
        comodel_name="agreement",
        inverse_name="purchase_order_id",
        string="Agreement",
        copy=False,
    )
    agreement_count = fields.Integer(
        compute="_compute_agreement_count",
    )
    po_type = fields.Selection(
        related="requisition_id.po_type",
    )

    @api.depends("agreement_ids")
    def _compute_agreement_count(self):
        for rec in self:
            rec.agreement_count = len(rec.agreement_ids)

    def action_view_agreement(self):
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "agreement_legal.agreement_operations_agreement"
        )
        agreements = self.agreement_ids
        if len(agreements) > 1:
            result["domain"] = [("id", "in", agreements.ids)]
        elif agreements:
            result["views"] = [
                (self.env.ref("agreement_legal.partner_agreement_form_view").id, "form")
            ]
            result["res_id"] = agreements.id
        return result

    def button_confirm(self):
        for rec in self:
            if rec.po_type == "agreement" and not rec.agreement_ids:
                raise UserError(_("No Agreement."))
        return super().button_confirm()
