# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


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
            elif (
                rec.payment_id and rec.payment_id.wt_tax_id.account_id == rec.account_id
            ):
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

    def _get_wt_amount(self, currency, wt_date):
        """ Calculate withholding tax and base amount based on currency """
        wt_lines = self.filtered("wt_tax_id")
        pit_lines = wt_lines.filtered("wt_tax_id.is_pit")
        wht_lines = wt_lines - pit_lines
        # Mixing PIT and WHT or > 1 type, no auto deduct
        if pit_lines and wht_lines:
            return (0, 0)
        # WHT
        if wht_lines:
            wht_tax = wht_lines.mapped("wt_tax_id")
            if len(wht_tax) != 1:
                return (0, 0)
            amount_base = 0
            amount_wt = 0
            for line in wht_lines:
                base_amount = line._get_wt_base_amount(currency, wt_date)
                amount_wt += line.wt_tax_id.amount / 100 * base_amount
                amount_base += base_amount
            return (amount_base, amount_wt)
        # PIT
        if pit_lines:
            pit_tax = pit_lines.mapped("wt_tax_id")
            pit_tax.ensure_one()
            move_lines = self.filtered(lambda l: l.wt_tax_id == pit_tax)
            amount_invoice_currency = sum(move_lines.mapped("amount_currency"))
            move = move_lines[0]
            company = move.company_id
            partner = move.partner_id
            # Convert invoice currency to payment currency
            amount_base = move.currency_id._convert(
                amount_invoice_currency, currency, company, wt_date
            )
            effective_pit = pit_tax.with_context(pit_date=wt_date).pit_id
            if not effective_pit:
                raise UserError(
                    _("No effective PIT rate for date %s")
                    % format_date(self.env, wt_date)
                )
            amount_wt = effective_pit._compute_expected_wt(
                partner,
                amount_base,
                pit_date=wt_date,
                currency=currency,
                company=company,
            )
            return (amount_base, amount_wt)
