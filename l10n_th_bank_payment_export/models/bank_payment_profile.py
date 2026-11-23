# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankPaymentProfile(models.Model):
    _name = "bank.payment.profile"
    _description = "Profile of Bank Payment"
    _check_company_auto = True

    name = fields.Char(required=True)
    bank = fields.Selection(
        selection=[],
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="bank.payment.profile.line",
        inverse_name="profile_id",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    journal_ids = fields.Many2many(
        comodel_name="account.journal",
    )


class BankPaymentProfileLine(models.Model):
    _name = "bank.payment.profile.line"
    _description = "Bank Payment Profile Line"

    profile_id = fields.Many2one(comodel_name="bank.payment.profile", index=True)
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        required=True,
        index=True,
        ondelete="cascade",
    )
    field_type = fields.Selection(related="field_id.ttype")
    value = fields.Char(required=True)
