# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentConfig(models.Model):
    _name = "bank.payment.config"
    _description = "Bank Payment Configuration"

    name = fields.Char(required=True)
    value = fields.Char(required=True)
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        required=True,
        index=True,
        domain=[
            ("model", "=", "bank.payment.export"),
            ("ttype", "=", "many2one"),
            ("relation", "=", "bank.payment.config"),
        ],
        ondelete="cascade",
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        index=True,
    )
    is_default = fields.Boolean(string="Default")

    @api.constrains("is_default", "journal_id")
    def check_is_default(self):
        BankConfig = self.env["bank.payment.config"]
        for rec in self:
            field_duplicate = BankConfig.search([("field_id", "=", rec.field_id.id)])
            if len(field_duplicate.filtered("is_default")) > 1:
                raise UserError(
                    _(
                        "You can not default field '{}' more than 1.".format(
                            rec.field_id.field_description
                        )
                    )
                )
            field_journal_duplicate = field_duplicate.filtered(
                lambda l: l.journal_id and l.journal_id == rec.journal_id
            )
            if len(field_journal_duplicate) > 1:
                raise UserError(_("Can not selected Journal more than 1."))
