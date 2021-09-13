# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare


class PersonalIncomeTax(models.Model):
    _name = "personal.income.tax"
    _description = "PIT Table"
    _rec_name = "calendar_year"

    calendar_year = fields.Char(
        required=True,
        default=lambda self: fields.Date.context_today(self).strftime("%Y"),
    )
    effective_date = fields.Date(
        string="Effective Date",
        compute="_compute_effective_date",
        store=True,
    )
    rate_ids = fields.One2many(
        comodel_name="personal.income.tax.rate",
        inverse_name="pit_id",
        string="Withholding Tax Rates",
    )
    active = fields.Boolean(default=True)

    @api.depends("calendar_year")
    def _compute_effective_date(self):
        for rec in self:
            rec.effective_date = "{}-01-01".format(rec.calendar_year)

    @api.constrains("rate_ids")
    def _check_rate_ids(self):
        for rec in self:
            prev_income_to = 0.0
            accum_tax = 0.0
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
                accum_tax += rate.amount_tax_max
                rate.amount_tax_max_accum = accum_tax

    def _compute_total_wht(self, rate_amount, tax_rate):
        return rate_amount * (tax_rate / 100)

    @api.model
    def calculate_rate_wht(self, total_income, income, date=False):
        if not date:
            date = fields.Date.context_today(self)
        calendar_year = date.strftime("%Y")
        pit = self.search(
            [("effective_date", "<=", date)], order="effective_date desc", limit=1
        )
        if not pit:
            raise ValidationError(
                _("No PIT Rate Table found for calendar year %s") % (calendar_year,)
            )
        rate_ranges = pit.rate_ids.filtered(lambda l: abs(total_income) > l.income_from)
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
    amount_tax_max_accum = fields.Float(
        string="Maximum Tax Accum",
        readonly=True,
    )

    @api.depends("income_from", "income_to", "tax_rate")
    def _compute_amount_tax_max(self):
        for rec in self:
            rec.amount_tax_max = (rec.income_to - rec.income_from) * (
                rec.tax_rate / 100
            )
