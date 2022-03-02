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
    is_default = fields.Boolean(string="Default")

    @api.constrains("is_default")
    def check_is_default(self):
        field_default_duplicate = self.env["bank.payment.config"].search(
            [
                ("field_id", "=", self.field_id.id),
                ("is_default", "=", True),
            ]
        )
        if len(field_default_duplicate) > 1:
            raise UserError(
                _(
                    "You can not default field '{}' more than 1.".format(
                        self.field_id.field_description
                    )
                )
            )
