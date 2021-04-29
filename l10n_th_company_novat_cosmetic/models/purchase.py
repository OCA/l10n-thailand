# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    cosmetic_vat = fields.Integer(
        string="Vat%",
        compute="_compute_cosmetic_vat",
        store=True,
        readonly=False,
        help="For VAT vendor and company No-VAT, show the cosmetic_vat",
    )
    company_novat = fields.Boolean(
        related="company_id.novat",
    )
    set_cosmetic_vat = fields.Boolean(
        string="Set Cosmetic VAT",
        help="Set to use Vat% to include VAT into price unit, "
        "and calculate cosmatic tax amount",
    )
    cosmetic_untaxed = fields.Monetary(
        string="(Untaxed)",
        store=True,
        readonly=False,
        compute="_compute_cosmetic",
    )
    cosmetic_tax = fields.Monetary(
        string="(Tax)",
        store=True,
        readonly=False,
        compute="_compute_cosmetic",
    )

    @api.depends("partner_id")
    def _compute_cosmetic_vat(self):
        for rec in self:
            if not rec.partner_id.novat and self.env.company.novat:
                rec.cosmetic_vat = self.env.company.account_purchase_tax_id.amount
            else:
                rec.cosmetic_vat = False

    @api.depends("set_cosmetic_vat", "amount_total")
    def _compute_cosmetic(self):
        for rec in self:
            cosmetic_vat = rec.cosmetic_vat if rec.set_cosmetic_vat else 0
            rec.cosmetic_tax = rec.amount_total * cosmetic_vat / (100 + cosmetic_vat)
            rec.cosmetic_untaxed = rec.amount_total - rec.cosmetic_tax

    @api.onchange("set_cosmetic_vat")
    def _onchange_set_cosmetic_vat(self):
        if self.set_cosmetic_vat:
            for line in self.order_line:
                line.cosmetic_price_unit = line.price_unit
                line._onchange_cosmetic_price_unit()
        else:
            for line in self.order_line:
                line.price_unit = line.cosmetic_price_unit


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    cosmetic_vat = fields.Integer(
        related="order_id.cosmetic_vat",
    )
    cosmetic_price_unit = fields.Float(string="(Price)")
    cosmetic_price_subtotal = fields.Monetary(
        string="(Subtotal)",
        compute="_compute_cosmetic",
        store=True,
        readonly=False,
    )

    @api.onchange("product_qty")
    def _onchange_cosmetic_product_qty(self):
        self.cosmetic_price_unit = False

    @api.onchange("cosmetic_price_unit", "product_qty")
    def _onchange_cosmetic_price_unit(self):
        if self.cosmetic_price_unit:
            self.price_unit = self.cosmetic_price_unit * (1 + self.cosmetic_vat / 100)

    @api.depends("cosmetic_price_unit", "product_qty")
    def _compute_cosmetic(self):
        for rec in self:
            rec.cosmetic_price_subtotal = rec.cosmetic_price_unit * rec.product_qty
