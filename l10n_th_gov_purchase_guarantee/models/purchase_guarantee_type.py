# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseGuaranteeType(models.Model):
    _name = "purchase.guarantee.type"
    _description = "Purchase Guarantee Type"

    name = fields.Char()
    is_create_invoice = fields.Boolean(
        string="Create Invoice ?",
        default=False,
    )
    active = fields.Boolean(
        default=True,
    )
