# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .withholding_tax_cert import WHT_CERT_INCOME_TYPE


class AccountWithholdingMove(models.Model):
    _name = "account.withholding.move"
    _description = "Withholding Tax Moves"

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
    )
    is_pit = fields.Boolean(
        related="wht_tax_id.is_pit",
        store=True,
    )
    wht_cert_income_type = fields.Selection(
        WHT_CERT_INCOME_TYPE,
        string="Type of Income",
    )
    wht_cert_income_desc = fields.Char(
        string="Income Description",
        size=500,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert",
        string="Withholding Cert.",
        readonly=True,
        copy=False,
    )

    @api.depends("move_id")
    def _compute_move_data(self):
        for rec in self:
            rec.date = rec.move_id and rec.move_id.date or False
            rec.calendar_year = rec.date and rec.date.strftime("%Y")
            rec.payment_id = rec.move_id.payment_id

    @api.onchange("wht_cert_income_type")
    def _onchange_wht_cert_income_type(self):
        if self.wht_cert_income_type:
            select_dict = dict(WHT_CERT_INCOME_TYPE)
            self.wht_cert_income_desc = select_dict[self.wht_cert_income_type]
        else:
            self.wht_cert_income_desc = False
