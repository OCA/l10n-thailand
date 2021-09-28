# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_wt_amount(self, currency, currency_date):
        """ Get WT Amount for case PIT """
        wt_taxes = self.mapped("wt_tax_id")
        # Normal WHT, call super()
        pit_tax = wt_taxes.filtered("account_pit")
        if not pit_tax:
            return super()._get_wt_amount(currency, currency_date)
        # Mixing PIT and WHT, no auto calc, because we can only withold 1 amount
        if pit_tax != wt_taxes:
            return (0, 0)
        # Calculate base amount and pit amount
        pit_tax.ensure_one()
        pit_date = currency_date
        move_lines = self.filtered(lambda l: l.wt_tax_id == pit_tax)
        amount_invoice_currency = sum(move_lines.mapped("amount_currency"))
        move = move_lines[0]
        company = move.company_id
        partner = move.partner_id
        # Convert invoice currency to payment currency
        amount_base = move.currency_id._convert(
            amount_invoice_currency, currency, company, pit_date
        )
        effective_pit = pit_tax.with_context(pit_date=pit_date).pit_id
        amount_pit = effective_pit._compute_expected_wt(
            partner, amount_base, pit_date=pit_date, currency=currency, company=company
        )
        return (amount_base, amount_pit)
