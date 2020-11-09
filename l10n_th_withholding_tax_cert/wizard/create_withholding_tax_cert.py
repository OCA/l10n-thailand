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
        required=True,
        help="If accounts are specified, system will auto fill tax amount",
        default=lambda self: self.env["account.account"].search(
            [("wt_account", "=", True)]
        ),
    )
    substitute = fields.Boolean(string="Substitute")
    wt_cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert",
        domain=[("state", "=", "done")],
        help="Withholding Tax is state 'done' only",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        model = self._context.get("active_model", False)
        if model == "account.move":
            active_id = self._context.get("active_id", False)
            move_id = self.env[model].browse(active_id)
            if move_id.type != "entry":
                raise UserError(
                    _(
                        "You can create withholding tax from "
                        "Payment or Journal Entry only."
                    )
                )
            if move_id.state != "posted":
                raise UserError(
                    _(
                        "You can create withholding tax from "
                        "Journal Entry state 'Paid' only."
                    )
                )
        return res

    def create_wt_cert(self):
        self.ensure_one()
        ctx = self._context.copy()
        model = ctx.get("active_model", False)
        active_id = ctx.get("active_id")
        object_id = self.env[model].browse(active_id)
        if len(ctx.get("active_ids", [])) != 1:
            raise ValidationError(_("Please select only 1 payment"))
        if model == "account.move":
            ctx.update(
                {
                    "default_move_id": active_id,
                    "wt_account_ids": self.wt_account_ids.ids,
                }
            )
        else:
            payment_wt = object_id.move_line_ids.filtered(
                lambda l: l.account_id.id in self.wt_account_ids.ids
            )
            if not payment_wt:
                raise UserError(
                    _(
                        "Can not create withholding tax cert. Selected account "
                        "does not match with Journal Items."
                    )
                )
            ctx.update(
                {
                    "default_payment_id": active_id,
                    "wt_account_ids": self.wt_account_ids.ids,
                }
            )
        # Substitute WT Cert
        if self.substitute:
            ctx.update({"wt_ref_id": self.wt_cert_id.id})
        return {
            "name": _("Create Withholding Tax Cert."),
            "view_mode": "form",
            "res_model": "withholding.tax.cert",
            "type": "ir.actions.act_window",
            "context": ctx,
        }
