# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .withholding_tax_cert import WHT_CERT_INCOME_TYPE


class PersonalIncomeTaxMove(models.Model):
    _name = "account.withholding.move"
    _description = "Personal Income Tax Move"

    payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        index=True,
        required=True,
        ondelete="cascade",
        domain=[("state", "not in", ["draft", "cancel"])],
    )
    payment_state = fields.Selection(related="payment_id.state")
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor",
        index=True,
        required=True,
        ondelete="cascade",
    )
    cancelled = fields.Boolean(readonly=True, help="For filtering cancelled payment")
    date = fields.Date(
        compute="_compute_date",
        store=True,
    )
    calendar_year = fields.Char(
        string="Calendar Year",
        compute="_compute_date",
        store=True,
        index=True,
    )
    amount_income = fields.Monetary(
        string="Income",
        required=True,
    )
    amount_wht = fields.Monetary(string="Withholding Amount")
    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        index=True,
    )
    is_pit = fields.Boolean(
        related="wht_tax_id.is_pit",
        store=True,
    )
    wht_cert_income_type = fields.Selection(
        WHT_CERT_INCOME_TYPE,
        string="Type of Income",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )

    @api.depends("payment_id")
    def _compute_date(self):
        for rec in self:
            rec.date = rec.payment_id and rec.payment_id.date or False
            rec.calendar_year = rec.date and rec.date.strftime("%Y")
