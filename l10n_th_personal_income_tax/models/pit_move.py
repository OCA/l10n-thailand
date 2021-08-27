# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ...l10n_th_withholding_tax_cert.models.withholding_tax_cert import (
    WHT_CERT_INCOME_TYPE,
)


class PersonalIncomeTaxMove(models.Model):
    _name = "pit.move"
    _description = "Personal Income Tax Move"
    # _order = "calendar_year, sequence, id"

    # sequence = fields.Char( # TODO: change it to code
    #     string='Sequence',
    #     readonly=True,
    #     size=500,
    # )
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
    #     posted = fields.Boolean(
    #         string='Posted',
    #         readonly=True,
    #         help="Once posted, sequence will run and WHT will be calculated"
    #     )
    cancelled = fields.Boolean(readonly=True, help="for filtered Payment is cancel")
    #     manual = fields.Boolean(
    #       help="Manually add line in Vendor window",
    #     )
    date = fields.Date(
        compute="_compute_date",
        store=True,
    )
    calendar_year = fields.Char(
        string="Calendar Year",
        compute="_compute_date",
        store=True,
    )
    amount_income = fields.Float(
        string="Income",
        required=True,
    )
    amount_wht = fields.Float(string="Withholding Amount")
    wht_cert_income_type = fields.Selection(
        WHT_CERT_INCOME_TYPE,
        string="Type of Income",
    )

    @api.depends("payment_id")
    def _compute_date(self):
        for rec in self:
            rec.date = rec.payment_id and rec.payment_id.date or False
            rec.calendar_year = rec.date and rec.date.strftime("%Y")


#     def unlink(self):
#         if len(self.filtered('posted')) > 0:
#             raise ValidationError(_('Posted records can not be deleted!'))
#         return super(PersonalIncomeTax, self).unlink()
