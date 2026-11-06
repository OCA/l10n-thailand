# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import format_date


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

    _effective_date_unique = models.Constraint(
        "UNIQUE(effective_date)",
        "Effective Date must be unique!",
    )

    @api.depends("calendar_year")
    def _compute_effective_date(self):
        for rec in self:
            year = rec.calendar_year or ""
            rec.effective_date = (
                f"{year}-01-01"
                if year.isdigit() and len(year) == 4 and not year.startswith("0")
                else False
            )

    def copy(self, default=None):
        self.ensure_one()
        default = dict(
            default or {},
            calendar_year=self.env._("%(year)s (copy)", year=self.calendar_year),
        )
        return super().copy(default)

    @api.constrains("rate_ids")
    def _check_rate_ids(self):
        for rec in self:
            prev_income_to = 0.0
            for i, rate in enumerate(rec.rate_ids):
                if i == 0 and rate.income_from != 0.0:
                    raise ValidationError(
                        self.env._("Income amount must start from 0.0")
                    )
                if i > 0 and float_compare(rate.income_from, prev_income_to, 2) != 0:
                    raise ValidationError(
                        self.env._(
                            "Discontinued income range!\n"
                            "Please make sure Income From = Previous Income To"
                        )
                    )
                prev_income_to = rate.income_to

    def _compute_total_wht(self, rate_amount, tax_rate):
        return rate_amount * (tax_rate / 100)

    def calculate_rate_wht(self, total_income, income, pit_date):
        self.ensure_one()
        # No tax while the yearly income is not above a range, also negative
        rate_ranges = self.rate_ids.filtered(
            lambda rate: total_income > rate.income_from
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

    @api.model
    def _get_effective_pit(self, pit_date):
        """PIT rate table effective on pit_date"""
        pit = self.search(
            [("effective_date", "<=", pit_date)], order="effective_date desc", limit=1
        )
        if not pit:
            raise UserError(
                self.env._(
                    "No effective PIT rate table for date %(date)s",
                    date=format_date(self.env, pit_date),
                )
            )
        return pit

    @api.model
    def _get_pit_income_domain(self, partner, company):
        """Posted PIT income of the partner: journal items of payments or
        journal entries carrying a PIT tax as base"""
        return [
            ("parent_state", "=", "posted"),
            ("move_id.move_type", "=", "entry"),
            ("move_id.tax_cash_basis_origin_move_id", "=", False),
            ("tax_repartition_line_id", "=", False),
            ("tax_ids.is_pit", "=", True),
            ("partner_id", "=", partner.id),
            ("company_id", "=", company.id),
        ]

    @api.model
    def _get_pit_amount_yearly(self, partner, pit_date, company=None):
        """PIT income of the partner accumulated in the calendar year of pit_date,
        in company currency"""
        company = company or self.env.company
        domain = self._get_pit_income_domain(partner, company) + [
            ("date", ">=", date(pit_date.year, 1, 1)),
            ("date", "<=", date(pit_date.year, 12, 31)),
        ]
        [(balance,)] = self.env["account.move.line"]._read_group(
            domain, aggregates=["balance:sum"]
        )
        return balance or 0.0


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

    @api.depends("pit_id.rate_ids.sequence", "pit_id.rate_ids.amount_tax_max")
    def _compute_amount_accum(self):
        """Maximum tax up to this rate, in the order of the rates of the table"""
        for rec in self:
            accum = 0.0
            for rate in rec.pit_id.rate_ids or rec:
                accum += rate.amount_tax_max
                if rate == rec:
                    break
            rec.amount_tax_accum = accum
