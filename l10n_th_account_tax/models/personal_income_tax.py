# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class PersonalIncomeTax(models.Model):
    _name = "personal.income.tax"
    _description = "PIT Table"
    _rec_name = "calendar_year"

    calendar_year = fields.Char(
        required=True,
        default=lambda self: fields.Date.context_today(self).strftime("%Y"),
        copy=False,
    )
    effective_date = fields.Date(
        compute="_compute_effective_date",
        store=True,
    )
    rate_ids = fields.One2many(
        comodel_name="personal.income.tax.rate",
        inverse_name="pit_id",
        string="Withholding Tax Rates",
        copy=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "effective_date_unique",
            "UNIQUE(effective_date)",
            "Effective Date must be unique!",
        ),
    ]

    @api.depends("calendar_year")
    def _compute_effective_date(self):
        for rec in self:
            rec.effective_date = False
            # Check len string (before convert) and digit int (after convert)
            if (
                rec.calendar_year.isdigit()
                and len(rec.calendar_year) == 4
                and len(str(int(rec.calendar_year))) == 4
            ):
                rec.effective_date = "{}-01-01".format(rec.calendar_year)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, calendar_year=_("%s (copy)") % self.calendar_year)
        return super().copy(default)

    @api.constrains("rate_ids")
    def _check_rate_ids(self):
        for rec in self:
            prev_income_to = 0.0
            for i, rate in enumerate(rec.rate_ids):
                if i == 0 and rate.income_from != 0.0:
                    raise UserError(_("Income amount must start from 0.0"))
                if i > 0 and float_compare(rate.income_from, prev_income_to, 2) != 0:
                    raise UserError(
                        _(
                            "Discontinued income range!\n"
                            "Please make sure Income From = Previous Income To"
                        )
                    )
                prev_income_to = rate.income_to

    def _compute_total_wht(self, rate_amount, tax_rate):
        return rate_amount * (tax_rate / 100)

    def calculate_rate_wht(self, total_income, income, pit_date):
        self.ensure_one()
        pit_date.strftime("%Y")
        rate_ranges = self.rate_ids.filtered(
            lambda l: abs(total_income) > l.income_from
        )
        current_amount = 0.0
        income_residual = income
        total_income_residual = total_income
        for rate_range in reversed(rate_ranges):
            rate_amount = total_income_residual - rate_range.income_from
            if income > rate_amount and income_residual >= rate_amount:
                total_income_residual -= rate_amount
                income_residual -= rate_amount
                current_amount += self._compute_total_wht(
                    rate_amount, rate_range.tax_rate
                )
            else:
                current_amount += self._compute_total_wht(
                    income_residual, rate_range.tax_rate
                )
                break
        return current_amount

    def _compute_expected_wht(self, partner, base_amount, pit_date, currency, company):
        """Calc PIT amount of a partner's yearly income"""
        self.ensure_one()
        pit_amount_year = self._get_pit_amount_yearly(partner, pit_date)
        # From currency to company currency
        base_amount = currency._convert(
            base_amount, company.currency_id, company, pit_date
        )
        # Calculate PIT amount from PIT Rate Table
        total_pit = pit_amount_year + base_amount
        expected_wht = self.calculate_rate_wht(total_pit, base_amount, pit_date)
        # From company currency to currency of base_amount
        expected_wht = company.currency_id._convert(
            expected_wht, currency, company, pit_date
        )
        return expected_wht

    @api.model
    def _get_pit_amount_yearly(self, partner, pit_date):
        calendar_year = pit_date.strftime("%Y")
        pit_year = partner.pit_move_ids.filtered(
            lambda l: l.calendar_year == calendar_year
        )
        return sum(pit_year.mapped("amount_income"))


class PersonalIncomeTaxRate(models.Model):
    _name = "personal.income.tax.rate"
    _description = "PIT Rates"
    _order = "sequence, id"

    sequence = fields.Integer(string="sequence")
    pit_id = fields.Many2one(
        comodel_name="personal.income.tax",
        string="PIT Table",
        ondelete="cascade",
        index=True,
    )
    income_from = fields.Float(
        string="Income From (>)",
    )
    income_to = fields.Float(
        string="Income To (<=)",
    )
    tax_rate = fields.Float(
        string="Tax Rate (%)",
    )
    amount_tax_max = fields.Float(
        string="Maximum Tax in Range",
        compute="_compute_amount_tax_max",
        store=True,
    )
    amount_tax_accum = fields.Float(
        string="Tax Accumulate",
        compute="_compute_amount_accum",
    )

    @api.depends("income_from", "income_to", "tax_rate")
    def _compute_amount_tax_max(self):
        for rec in self:
            rec.amount_tax_max = (rec.income_to - rec.income_from) * (
                rec.tax_rate / 100
            )

    def _compute_amount_accum(self):
        for rec in self:
            prev_rec = self.filtered(lambda l: l.sequence <= rec.sequence)
            rec.amount_tax_accum = sum(prev_rec.mapped("amount_tax_max"))
