# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    wt_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="payment_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )

    @api.multi
    def button_wt_certs(self):
        return {
            "name": _("Withholding Tax Certs."),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.wt_cert_ids.ids)],
        }
