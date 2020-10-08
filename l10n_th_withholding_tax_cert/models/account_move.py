# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    wt_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="move_id",
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
        return {
            "name": _("Withholding Tax Certs."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.wt_cert_ids.ids)],
        }
