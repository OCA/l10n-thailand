# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "base.cosmetic.vat"]
    _line_field = "invoice_line_ids"
    _partner_field = "partner_id"

    @api.onchange("partner_id")
    def _onchange_cosmetic_vat(self):
        super()._onchange_cosmetic_vat()


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "base.cosmetic.vat.line"]
    _inverse_field = "move_id"
    _price_field = "price_unit"
    _subtotal_field = "price_subtotal"
    _quantity_field = "quantity"

    cosmetic_vat = fields.Integer(
        related="move_id.cosmetic_vat",
    )

    @api.onchange("quantity", "price_unit")
    def _onchange_cosmetic_product_qty(self):
        super()._onchange_cosmetic_product_qty()

    @api.depends("cosmetic_price_unit", "quantity")
    def _compute_cosmetic_subtotal(self):
        super()._compute_cosmetic_subtotal()
