# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.withholding_tax_cert import INCOME_TAX_FORM, WHT_CERT_INCOME_TYPE


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
    # Used for create multi certs
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM, string="Income Tax Form"
    )
    wt_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income"
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        model = self._context.get("active_model", False)
        for active_id in self._context.get("active_ids", []):
            if model == "account.move":
                move = self.env[model].browse(active_id)
                if move.move_type != "entry":
                    raise UserError(
                        _(
                            "You can create withholding tax from "
                            "Payment or Journal Entry only."
                        )
                    )
                if move.state != "posted":
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
            raise ValidationError(_("Please select only 1 document"))
        if model == "account.move":
            ctx.update(
                {
                    "default_move_id": active_id,
                    "wt_account_ids": self.wt_account_ids.ids,
                }
            )
        else:
            payment_wt = object_id.move_id.line_ids.filtered(
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
        # Other defaults
        ctx.update(
            {
                "income_tax_form": self.income_tax_form,
                "wt_cert_income_type": self.wt_cert_income_type,
            }
        )
        return {
            "name": _("Create Withholding Tax Cert."),
            "view_mode": "form",
            "res_model": "withholding.tax.cert",
            "type": "ir.actions.act_window",
            "context": ctx,
        }

    def create_wt_cert_multi(self):
        ctx = self._context.copy()
        active_ids = ctx.get("active_ids")
        Cert = self.env["withholding.tax.cert"]
        cert_ids = []
        for active_id in active_ids:
            ctx.update(
                {"active_id": active_id, "active_ids": [active_id]}
            )  # Mock single cert.
            res = self.with_context(ctx).create_wt_cert()
            # Create new withholding.tax.cert
            cert = Cert.with_context(res["context"]).new()
            cert._compute_wt_cert_data()
            new_cert = Cert.create(cert._convert_to_write(cert._cache))
            cert_ids.append(new_cert.id)
        return {
            "name": _("Create Multi Withholding Tax Cert."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", cert_ids)],
        }
