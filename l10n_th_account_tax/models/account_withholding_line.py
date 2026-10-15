# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountWithholdingLine(models.AbstractModel):
    _inherit = "account.withholding.line"

    def _get_pit_sibling_lines(self):
        """Withholding lines of the same payment (or payment register)"""
        return self

    def _compute_pit_amounts(self):
        """Progressive PIT of the PIT lines of one payment, on the yearly income
        of the partner. Each line gets the difference of rounded running totals,
        so that the total PIT does not depend on how lines are split.

        :return: {line: amount in payment currency}
        """
        if not self:
            return {}
        first = self[0]
        company = first.company_id or self.env.company
        pit_date = first.comodel_date or fields.Date.context_today(self)
        currency = first.comodel_currency_id or company.currency_id
        company_currency = company.currency_id
        pit = self.env["personal.income.tax"]._get_effective_pit(pit_date)
        income_year = pit._get_pit_amount_yearly(
            first._get_comodel_partner(), pit_date, company
        )
        amounts = {}
        running_base = 0.0
        previous_tax = 0.0
        for line in self:
            running_base += currency._convert(
                line.base_amount, company_currency, company, pit_date
            )
            running_tax = pit.calculate_rate_wht(
                income_year + running_base, running_base, pit_date
            )
            running_tax = company_currency._convert(
                running_tax, currency, company, pit_date
            )
            amounts[line] = running_tax - previous_tax
            previous_tax = running_tax
        return amounts

    @api.depends("comodel_date", "comodel_currency_id")
    def _compute_amount(self):
        pit_lines = self.filtered("tax_id.is_pit")
        res = super(AccountWithholdingLine, self - pit_lines)._compute_amount()
        done = self.browse()
        for line in pit_lines:
            if line in done:
                continue
            siblings = line._get_pit_sibling_lines().filtered("tax_id.is_pit")
            amounts = siblings._compute_pit_amounts()
            for pit_line in siblings & pit_lines:
                pit_line.amount = amounts[pit_line]
            done |= siblings
        return res


class AccountPaymentWithholdingLine(models.Model):
    _inherit = "account.payment.withholding.line"

    def _get_pit_sibling_lines(self):
        return self.payment_id.withholding_line_ids

    @api.depends("payment_id.partner_id", "payment_id.withholding_line_ids.base_amount")
    def _compute_amount(self):
        return super()._compute_amount()
