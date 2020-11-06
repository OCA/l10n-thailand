# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_th_withholding_tax_cert.models.withholding_tax_cert import (
    INCOME_TAX_FORM,
    WHT_CERT_INCOME_TYPE,
)


class CreateWithholdingTaxCert(models.TransientModel):
    _inherit = "create.withholding.tax.cert"

    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM, string="Income Tax Form"
    )
    wt_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income"
    )

    def create_wt_cert_multi(self):
        self.ensure_one()
        WithholdingTaxCert = self.env["withholding.tax.cert"]
        WithholdingTaxCertLine = self.env["withholding.tax.cert.line"]
        ctx = self._context.copy()
        ctx.update(
            {
                "wt_account_ids": self.wt_account_ids.ids,
                "wt_cert_income_type": self.wt_cert_income_type,
            }
        )
        wht_certs = []
        active_ids = ctx.get("active_ids", [])
        active_model = ctx.get("active_model", False)
        docs = self.env[active_model].browse(active_ids)
        for doc in docs:
            vals = {
                "name": doc.name,
                "income_tax_form": self.income_tax_form,
            }
            if active_model == "account.move":
                partner = doc.line_ids.filtered(
                    lambda l: l.account_id in self.wt_account_ids
                ).mapped("partner_id")
                if len(partner) != 1:
                    raise UserError(_("No single partner to create WHT Cert."))
                vals.update(
                    {
                        "move_id": doc.id,
                        "date": doc.date,
                        "supplier_partner_id": partner.id,
                    }
                )
            elif active_model == "account.payment":
                payment_wt = doc.move_line_ids.filtered(
                    lambda l: l.account_id.id in self.wt_account_ids.ids
                )
                if not payment_wt:
                    raise UserError(
                        _(
                            "Can not create withholding tax cert. Selected account "
                            "does not match with Journal Items."
                        )
                    )
                vals.update(
                    {
                        "payment_id": doc.id,
                        "date": doc.payment_date,
                        "supplier_partner_id": doc.partner_id.id,
                    }
                )
            wht_cert = WithholdingTaxCert.with_context(ctx).create(vals)
            wt_move_lines = wht_cert._get_wt_move_line(
                wht_cert.payment_id, wht_cert.move_id, self.wt_account_ids.ids
            )
            for line in wt_move_lines:
                wht_cert.wt_line += WithholdingTaxCertLine.create(
                    wht_cert.with_context(ctx)._prepare_wt_line(line)
                )
            wht_certs.append(wht_cert.id)
        return {
            "name": _("Create Multi Withholding Tax Cert."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", wht_certs)],
        }
