# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class BaseCosmeticVAT(models.AbstractModel):
    _name = "base.cosmetic.vat"
    _description = "Base Cosmetic VAT"
    _line_field = False
    _partner_field = False

    company_novat = fields.Boolean(
        default=lambda self: self.env.company.novat,
    )
    cosmetic_vat = fields.Integer(
        string="Vat%:",
        help="For VAT vendor and company No-VAT, show the cosmetic_vat",
    )
    set_cosmetic_vat = fields.Boolean(
        string="Set Cosmetic VAT",
        help="Set to use Vat% to include VAT into price unit, "
        "and calculate cosmatic tax amount",
    )
    cosmetic_untaxed = fields.Float(
        string="(Untaxed)",
        store=True,
        readonly=False,
        compute="_compute_cosmetic_footer",
    )
    cosmetic_tax = fields.Float(
        string="(Tax)",
        store=True,
        readonly=False,
        compute="_compute_cosmetic_footer",
    )

    @api.depends("set_cosmetic_vat")
    def _compute_cosmetic_footer(self):
        for rec in self:
            untaxed = 0
            for line in rec[self._line_field]:
                untaxed += line.cosmetic_price_subtotal or line[line._subtotal_field]
            total = sum(
                rec[self._line_field].mapped(rec[self._line_field]._subtotal_field)
            )
            rec.cosmetic_tax = total - untaxed
            rec.cosmetic_untaxed = untaxed

    def _onchange_cosmetic_vat(self):
        if not self.mapped(self._partner_field).novat and self.env.company.novat:
            self.cosmetic_vat = self.env.company.account_purchase_tax_id.amount
        else:
            self.cosmetic_vat = False

    def apply_cosmetic_vat(self):
        self.mapped(self._line_field).apply_cosmetic_vat()
        self.write({"set_cosmetic_vat": True})

    def remove_cosmetic_vat(self):
        self.mapped(self._line_field).remove_cosmetic_vat()
        self.write({"set_cosmetic_vat": False})


class BaseCosmeticVATLine(models.AbstractModel):
    _name = "base.cosmetic.vat.line"
    _description = "Base Cosmetic VAT Line"
    _inverse_field = False
    _subtotal_field = False
    _price_field = False
    _quantity_field = False

    cosmetic_vat = fields.Integer()
    set_cosmetic_vat = fields.Boolean()
    cosmetic_price_unit = fields.Float(string="(Price)")
    cosmetic_price_subtotal = fields.Float(
        string="(Subtotal)",
        compute="_compute_cosmetic_subtotal",
        store=True,
        readonly=False,
    )

    def _onchange_cosmetic_product_qty(self):
        if self._origin.cosmetic_vat:
            self.cosmetic_vat = False
            self.cosmetic_price_unit = False

    def apply_cosmetic_vat(self):
        self = self.with_context(check_move_validity=False)
        for rec in self.filtered(lambda l: not l.set_cosmetic_vat):
            rec.cosmetic_price_unit = rec[rec._price_field]
            rec[rec._price_field] = rec.cosmetic_price_unit * (
                1 + rec.cosmetic_vat / 100
            )
            rec[self._inverse_field]._compute_cosmetic_footer()
            if self._name == "account.move.line":
                rec[self._inverse_field]._recompute_dynamic_lines()
        self.write({"set_cosmetic_vat": True})

    def remove_cosmetic_vat(self):
        self = self.with_context(check_move_validity=False)
        for rec in self.filtered(lambda l: l.set_cosmetic_vat):
            rec[rec._price_field] = rec.cosmetic_price_unit
            rec.cosmetic_price_unit = False
            rec[self._inverse_field]._compute_cosmetic_footer()
            if self._name == "account.move.line":
                rec[self._inverse_field]._recompute_dynamic_lines()
        self.write({"set_cosmetic_vat": False})

    def _compute_cosmetic_subtotal(self):
        for rec in self:
            rec.cosmetic_price_subtotal = (
                rec.cosmetic_price_unit * rec[rec._quantity_field]
            )
