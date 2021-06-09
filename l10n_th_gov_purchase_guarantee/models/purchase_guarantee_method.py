# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseGuaranteeMethod(models.Model):
    _name = "purchase.guarantee.method"
    _description = "Purchase Guarantee Method"

    name = fields.Char(
        string="Name",
    )
    default_for_model = fields.Selection(
        selection=[
            ("purchase.requisition", "Purchase Agreement"),
            ("purchase.order.rfq", "Request for Quotation"),
            ("purchase.order.po", "Purchase Order"),
        ],
        string="Default method for",
        help="Guarantee created from which document model, will use this method",
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        index=True,
        ondelete="restrict",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
