# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    cosmetic_vat = fields.Integer(
        string="Vat%",
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
        compute="_compute_cosmetic_footer",
    )
    cosmetic_tax = fields.Monetary(
        string="(Tax)",
        store=True,
        readonly=False,
        compute="_compute_cosmetic_footer",
    )

    @api.depends("set_cosmetic_vat")
    def _compute_cosmetic_footer(self):
        for rec in self:
            untaxed = 0
            for line in rec.invoice_line_ids:
                untaxed += line.cosmetic_price_subtotal or line.price_subtotal
            total = sum(rec.invoice_line_ids.mapped("price_subtotal"))
            rec.cosmetic_tax = total - untaxed
            rec.cosmetic_untaxed = untaxed

    @api.onchange("partner_id")
    def _onchange_cosmetic_vat(self):
        if not self.partner_id.novat and self.env.company.novat:
            self.cosmetic_vat = self.env.company.account_purchase_tax_id.amount
        else:
            self.cosmetic_vat = False

    def apply_cosmetic_vat(self):
        self.mapped("invoice_line_ids").apply_cosmetic_vat()
        self.write({"set_cosmetic_vat": True})

    def remove_cosmetic_vat(self):
        self.mapped("invoice_line_ids").remove_cosmetic_vat()
        self.write({"set_cosmetic_vat": False})


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cosmetic_vat = fields.Integer(
        related="move_id.cosmetic_vat",
    )
    set_cosmetic_vat = fields.Boolean()
    cosmetic_price_unit = fields.Float(string="(Price)")
    cosmetic_price_subtotal = fields.Monetary(
        string="(Subtotal)",
        compute="_compute_cosmetic_subtotal",
        store=True,
        readonly=False,
    )

    @api.onchange("quantity", "price_unit")
    def _onchange_cosmetic_product_qty(self):
        if self._origin.cosmetic_vat:
            self.cosmetic_vat = False
            self.cosmetic_price_unit = False

    def apply_cosmetic_vat(self):
        self = self.with_context(check_move_validity=False)
        for rec in self.filtered(lambda l: not l.set_cosmetic_vat):
            rec.cosmetic_price_unit = rec.price_unit
            rec.price_unit = rec.cosmetic_price_unit * (1 + rec.cosmetic_vat / 100)
            rec.move_id._compute_cosmetic_footer()
            rec.move_id._recompute_dynamic_lines()
        self.write({"set_cosmetic_vat": True})

    def remove_cosmetic_vat(self):
        self = self.with_context(check_move_validity=False)
        for rec in self.filtered(lambda l: l.set_cosmetic_vat):
            rec.price_unit = rec.cosmetic_price_unit
            rec.cosmetic_price_unit = False
            rec.move_id._compute_cosmetic_footer()
            rec.move_id._recompute_dynamic_lines()
        self.write({"set_cosmetic_vat": False})

    @api.depends("cosmetic_price_unit", "quantity")
    def _compute_cosmetic_subtotal(self):
        for rec in self:
            rec.cosmetic_price_subtotal = rec.cosmetic_price_unit * rec.quantity
