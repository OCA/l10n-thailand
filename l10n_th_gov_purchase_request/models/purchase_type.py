# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseType(models.Model):
    _name = "purchase.type"
    _description = "Type of purchase"
    _order = "sequence"

    name = fields.Char(
        required=True,
    )
    code = fields.Char()
    active = fields.Boolean(
        default=True,
    )
    description = fields.Text(
        translate=True,
    )
    sequence = fields.Integer(
        default=10,
    )
    to_create = fields.Selection(
        selection=[
            ("purchase_agreement", "Purchase Agreement"),
            ("expense", "Expense"),
        ],
        required=True,
        help="Create purchase agreement or expense when pr is approved",
    )
    is_default = fields.Boolean(
        string="Default",
        default=False,
        help="Default purchase type on the purchase request",
    )
    procurement_method_ids = fields.Many2many(
        comodel_name="procurement.method",
        string="Allowed Procurement Method",
        required=True,
        help="This field will help to filter procurement method in each purchase type "
        "on the purchase request",
    )

    @api.constrains("active", "is_default")
    def _check_is_default(self):
        purchase_types = self.env["purchase.type"].search([("is_default", "=", True)])
        if len(purchase_types) > 1:
            raise UserError(_("Purchase type must have only one default."))
