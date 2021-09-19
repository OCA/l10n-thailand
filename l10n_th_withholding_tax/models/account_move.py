# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WT",
        compute="_compute_wt_tax_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "account_id")
    def _compute_wt_tax_id(self):
        for rec in self:
            # From invoice, default from product
            if rec.move_id.move_type in ("out_invoice", "out_refund", "in_receipt"):
                rec.wt_tax_id = rec.product_id.wt_tax_id
            elif rec.move_id.move_type in ("in_invoice", "in_refund", "out_receipt"):
                rec.wt_tax_id = rec.product_id.supplier_wt_tax_id
            elif rec.payment_id:
                rec.wt_tax_id = rec.payment_id.wt_tax_id
            else:
                rec.wt_tax_id = False

    def _get_wt_base_amount(self, currency, currency_date):
        self.ensure_one()
        wt_base_amount = 0
        if not currency or self.currency_id == currency:
            # Same currency
            wt_base_amount = self.amount_currency
        elif currency == self.company_currency_id:
            # Payment expressed on the company's currency.
            wt_base_amount = self.balance
        else:
            # Foreign currency on payment different than the one set on the journal entries.
            wt_base_amount = self.company_currency_id._convert(
                self.balance, currency, self.company_id, currency_date
            )
        return wt_base_amount
