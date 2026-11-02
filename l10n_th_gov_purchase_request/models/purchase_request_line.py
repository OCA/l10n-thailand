# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    product_id = fields.Many2one(
        compute="_compute_default_product_id",
        store=True,
        readonly=False,
    )

    @api.depends("request_id")
    def _compute_default_product_id(self):
        for rec in self:
            rec.product_id = rec.request_id.procurement_type_id.product_id
