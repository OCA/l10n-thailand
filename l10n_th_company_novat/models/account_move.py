# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "base.company.novat"]
    _tax_field_name = "tax_ids"

    wtvat = fields.Float(
        string="Vat%",
        compute="_compute_wtvat",
        store=True,
        readonly=False,
        copy=True,
        help="Only with No-VAT registered company, set default tax  "
        "to calculate base amount used for withholding amount",
    )

    @api.depends("move_id.partner_id")
    def _compute_wtvat(self):
        if not self.env.company.novat:
            self.update({"wtvat": False})
            return
        for rec in self:
            partner = rec.move_id.partner_id
            percent = False
            if partner and not partner.novat:  # VAT partner
                move_type = rec.move_id.move_type
                if move_type in ("out_invoice", "out_refund"):
                    percent = self.env.company.account_sale_tax_id.amount
                if move_type in ("in_invoice", "in_refund"):
                    percent = self.env.company.account_purchase_tax_id.amount
            rec.wtvat = percent

    def _get_wt_base_amount(self):
        """ Use wtvat percent, to calculate the base_amout for WHT """
        price_subtotal = super()._get_wt_base_amount()
        return price_subtotal * 100 / (100 + self.wtvat)
