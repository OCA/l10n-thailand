# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CreateWithholdingTaxCert(models.TransientModel):
    _name = "create.withholding.tax.cert"
    _description = "Create Withholding Tax Cert Wizard"

    wt_account_ids = fields.Many2many(
        comodel_name="account.account",
        string="Withholing Tax Accounts",
        help="If accounts are specified, system will auto fill tax amount",
        default=lambda self: self.env["account.account"].search(
            [("wt_account", "=", True)]
        ),
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        model = self._context.get("active_model", False)
        if model == "account.move":
            active_ids = self._context.get("active_ids", False)
            move_ids = self.env[model].browse(active_ids)
            not_entry = move_ids.filtered(lambda l: l.type != "entry")
            if not_entry:
                raise UserError(
                    _(
                        "You can create withholding tax from "
                        "Payment or Journal Entry only."
                    )
                )
        return res

    def create_wt_cert(self):
        self.ensure_one()
        ctx = self._context.copy()
        model = ctx.get("active_model", False)
        if len(ctx.get("active_ids", [])) != 1:
            raise ValidationError(_("Please select only 1 payment"))
        if model == "account.move":
            ctx.update(
                {
                    "default_move_id": ctx.get("active_id"),
                    "wt_account_ids": self.wt_account_ids.ids,
                }
            )
        else:
            ctx.update(
                {
                    "default_payment_id": ctx.get("active_id"),
                    "wt_account_ids": self.wt_account_ids.ids,
                }
            )
        return {
            "name": _("Create Withholding Tax Cert."),
            "view_mode": "form",
            "res_model": "withholding.tax.cert",
            "type": "ir.actions.act_window",
            "context": ctx,
        }
