# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProcurementMethod(models.Model):
    _name = "procurement.method"
    _description = "Procurement Method"
    _order = "sequence"

    name = fields.Char(
        string="Name",
        required=True,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    description = fields.Text(
        string="Description",
        translate=True,
    )
