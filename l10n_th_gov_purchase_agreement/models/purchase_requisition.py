# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    po_type = fields.Selection(
        selection=[
            ("agreement", "Agreement"),
            ("no_agreement", "No Agreement"),
        ],
        string="PO Type",
        copy=False,
        tracking=True,
    )
