# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProcurementType(models.Model):
    _name = "procurement.type"
    _description = "Procurement Method"
    _order = "sequence"

    name = fields.Char(
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        help="Default product for purchase request line",
    )
    active = fields.Boolean(
        default=True,
    )
    sequence = fields.Integer(
        default=10,
    )
    description = fields.Text(
        translate=True,
    )
