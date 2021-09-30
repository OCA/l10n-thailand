# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    wt_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="payment_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )
    wt_cert_cancel = fields.Boolean(
        compute="_compute_wt_cert_cancel",
        store=True,
        help="This document has WT Cert(s) and all are cancelled or not WT Cert",
    )

    @api.depends("wt_cert_ids.state")
    def _compute_wt_cert_cancel(self):
        for record in self:
            wt_state = list(set(record.wt_cert_ids.mapped("state")))
            wt_cancel = False
            if not wt_state or (len(wt_state) == 1 and "cancel" in wt_state):
                wt_cancel = True
            record.wt_cert_cancel = wt_cancel

    def button_wt_certs(self):
        self.ensure_one()
        action = self.env.ref(
            "l10n_th_withholding_tax_cert.action_withholding_tax_cert_menu"
        )
        result = action.sudo().read()[0]
        result["domain"] = [("id", "in", self.wt_cert_ids.ids)]
        return result
