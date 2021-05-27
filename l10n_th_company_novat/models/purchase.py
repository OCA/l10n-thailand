# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "base.company.novat"]
    _tax_field_name = "taxes_id"
