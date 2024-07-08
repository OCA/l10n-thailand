# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .withholding_tax_cert import WHT_CERT_INCOME_TYPE


class AccountWithholdingMove(models.Model):
    _name = "account.withholding.move"
    _description = "Withholding Tax Moves"
    _check_company_auto = True

    payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        index=True,
        ondelete="cascade",
        domain=[("state", "not in", ["draft", "cancel"])],
        compute="_compute_move_data",
        store=True,
        readonly=False,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
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
        compute="_compute_move_data",
        store=True,
        readonly=False,
    )
    calendar_year = fields.Char(
        compute="_compute_move_data",
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
        check_company=True,
    )
    is_pit = fields.Boolean(
        related="wht_tax_id.is_pit",
        store=True,
    )
    wht_cert_income_type = fields.Selection(
        WHT_CERT_INCOME_TYPE,
        string="Type of Income",
        compute="_compute_wht_cert_income_type",
        store=True,
        readonly=False,
    )
    wht_cert_income_desc = fields.Char(
        string="Income Description",
        size=500,
        compute="_compute_wht_cert_income_desc",
        store=True,
        readonly=False,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert",
        string="Withholding Cert.",
        readonly=True,
        copy=False,
        check_company=True,
    )

    @api.depends("move_id")
    def _compute_move_data(self):
        for rec in self:
            rec.date = rec.move_id and rec.move_id.date or False
            rec.calendar_year = rec.date and rec.date.strftime("%Y")
            rec.payment_id = rec.move_id.payment_id

    @api.depends("wht_tax_id")
    def _compute_wht_cert_income_type(self):
        for rec in self:
            rec.wht_cert_income_type = (
                rec.wht_tax_id and rec.wht_tax_id.wht_cert_income_type or False
            )

    @api.depends("wht_cert_income_type")
    def _compute_wht_cert_income_desc(self):
        for rec in self:
            if rec.wht_cert_income_type:
                select_dict = dict(WHT_CERT_INCOME_TYPE)
                rec.wht_cert_income_desc = select_dict[rec.wht_cert_income_type]
            else:
                rec.wht_cert_income_desc = False
