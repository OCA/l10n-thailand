# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_guarantee_ids = fields.One2many(
        comodel_name="purchase.guarantee",
        inverse_name="purchase_id",
        string="Guarantee",
    )
    purchase_guarantee_count = fields.Integer(
        string="Guarantee Count",
        compute="_compute_purchase_guarantee_count",
    )

    @api.depends("purchase_guarantee_ids")
    def _compute_purchase_guarantee_count(self):
        for rec in self:
            rec.purchase_guarantee_count = len(rec.purchase_guarantee_ids)

    def action_view_purchase_guarantee(self):
        self.ensure_one()
        action = self.env.ref(
            "l10n_th_gov_purchase_guarantee.purchase_guarantee_action"
        )
        result = action.sudo().read()[0]
        result["domain"] = [("purchase_id", "=", self.id)]
        result["context"] = {
            "default_reference": "purchase.order,%s" % (str(self.id),),
        }
        return result
