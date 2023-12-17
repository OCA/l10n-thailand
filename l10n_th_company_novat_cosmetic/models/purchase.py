# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "base.cosmetic.vat"]
    _line_field = "order_line"
    _partner_field = "partner_id"

    @api.onchange("partner_id")
    def _onchange_cosmetic_vat(self):
        super()._onchange_cosmetic_vat()


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "base.cosmetic.vat.line"]
    _inverse_field = "order_id"
    _price_field = "price_unit"
    _subtotal_field = "price_subtotal"
    _quantity_field = "product_qty"

    cosmetic_vat = fields.Integer(
        related="order_id.cosmetic_vat",
    )

    @api.onchange("product_qty", "price_unit")
    def _onchange_cosmetic_product_qty(self):
        super()._onchange_cosmetic_product_qty()

    @api.depends("cosmetic_price_unit", "product_qty")
    def _compute_cosmetic_subtotal(self):
        super()._compute_cosmetic_subtotal()
