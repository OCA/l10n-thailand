# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # Default location is customer location
        company_id = res.get("company_id", False)
        company = self.env["res.company"].browse(company_id)
        customer_location = self.env["stock.location"].search(
            [("company_id", "in", (company_id, False)), ("usage", "=", "customer")],
            limit=1,
        )
        if not company or company.stock_request_allow_virtual_loc and customer_location:
            res["location_id"] = customer_location.id
        return res

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        if not self.location_id.warehouse_id:
            return
        super().onchange_warehouse_id()
