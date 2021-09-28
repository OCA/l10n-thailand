# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    def action_create_pit_withholding_tax_cert(self):
        view = "l10n_th_withholding_tax_pit.create_pit_withholding_tax_cert"
        return {
            "name": _("Create Withholding Tax Cert."),
            "res_model": "create.pit.withholding.tax.cert",
            "view_mode": "form",
            "view_id": self.env.ref(view).id,
            "context": self.env.context,
            "target": "new",
            "type": "ir.actions.act_window",
        }
