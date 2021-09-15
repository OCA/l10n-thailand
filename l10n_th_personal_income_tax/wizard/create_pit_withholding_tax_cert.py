# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_th_withholding_tax_cert.models.withholding_tax_cert import (
    INCOME_TAX_FORM,
    WHT_CERT_INCOME_TYPE,
)


class CreatePITWithholdingTaxCert(models.TransientModel):
    _name = "create.pit.withholding.tax.cert"
    _description = "Create Withholding Tax Cert Wizard From PIT"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM,
        string="Income Tax Form",
        required=True,
    )
    payment_date = fields.Date(default=fields.Date.today(), required=True)

    def _prepare_wt_line(self, cert, partner_id):
        CertLine = self.env["withholding.tax.cert.line"]
        select_dict = dict(WHT_CERT_INCOME_TYPE)
        pit_line = partner_id.pit_line.filtered(
            lambda l: self.date_from <= l.date <= self.date_to
            and l.payment_state == "posted"
        )
        for line in pit_line:
            cert.wt_line += CertLine.new(
                {
                    "wt_cert_income_type": line.wt_cert_income_type,
                    "wt_cert_income_desc": select_dict[line.wt_cert_income_type],
                    "base": line.amount_income,
                    "amount": abs(line.amount_wt),
                }
            )

    def create_pit_wt_cert(self):
        self.ensure_one()
        ctx = self._context.copy()
        model = ctx.get("active_model", False)
        active_id = ctx.get("active_id")
        Cert = self.env["withholding.tax.cert"]
        cert_ids = []
        if model != "res.partner":
            raise UserError(
                _("You can create pit withholding tax from partner view only.")
            )
        partner_id = self.env[model].browse(active_id)
        # Create new withholding.tax.cert
        cert = Cert.new()
        cert.write(
            {
                "supplier_partner_id": partner_id.id,
                "income_tax_form": self.income_tax_form,
                "date": self.payment_date,
            }
        )
        self._prepare_wt_line(cert, partner_id)
        new_cert = Cert.create(cert._convert_to_write(cert._cache))
        cert_ids.append(new_cert.id)
        return {
            "name": _("Create PIT Withholding Tax Cert."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", cert_ids)],
        }
