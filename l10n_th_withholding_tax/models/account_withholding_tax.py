# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountWithholdingTax(models.Model):
    _name = "account.withholding.tax"
    _description = "Account Withholding Tax"

    name = fields.Char(required=True)
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Withholding Tax Account",
        domain=[("wt_account", "=", True)],
        required=True,
        ondelete="restrict",
    )
    amount = fields.Float(string="Amount",)

    @api.constrains("account_id")
    def _check_account_id(self):
        for rec in self:
            if rec.account_id and not rec.account_id.wt_account:
                raise ValidationError(_("Selected account is not for withholding tax"))
