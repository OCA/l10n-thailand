# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Agreement(models.Model):
    _inherit = "agreement"

    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="RFQ",
        index=True,
        tracking=True,
        copy=False,
        domain="[('state', 'in', ['draft', 'sent']), ('po_type', '=', 'agreement')]",
    )
    use_invoice_plan = fields.Boolean(
        related="purchase_order_id.use_invoice_plan",
    )
    invoice_plan_ids = fields.Many2many(
        comodel_name="purchase.invoice.plan",
        compute="_compute_invoice_plan_ids",
        inverse="_inverse_invoice_plan_ids",
    )

    @api.depends("purchase_order_id")
    def _compute_invoice_plan_ids(self):
        for rec in self:
            rec.invoice_plan_ids = rec.purchase_order_id.invoice_plan_ids

    def _inverse_invoice_plan_ids(self):
        for rec in self:
            rec.purchase_order_id.invoice_plan_ids = rec.invoice_plan_ids

    @api.onchange("purchase_order_id")
    def _onchange_purchase_id(self):
        self.partner_id = self.purchase_order_id.partner_id

    @api.constrains("purchase_order_id")
    def _check_partner(self):
        for rec in self:
            if (
                rec.purchase_order_id
                and rec.purchase_order_id.partner_id != rec.partner_id
            ):
                raise UserError(_("The partner should be the same as in RFQ."))
