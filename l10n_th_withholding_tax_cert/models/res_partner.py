# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def button_wt_certs(self):
        self.ensure_one()
        action = self.env.ref(
            "l10n_th_withholding_tax_cert.action_withholding_tax_cert_menu"
        )
        result = action.sudo().read()[0]
        certs = self.env["withholding.tax.cert"].search(
            [("supplier_partner_id", "=", self.id)]
        )
        result["domain"] = [("id", "in", certs.ids)]
        return result
