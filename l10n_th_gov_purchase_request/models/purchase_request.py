# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    procurement_type_id = fields.Many2one(
        comodel_name="procurement.type",
        string="Procurement Type",
        ondelete="restrict",
        index=True,
    )
    purchase_type_id = fields.Many2one(
        comodel_name="purchase.type",
        string="Purchase Type",
        ondelete="restrict",
        index=True,
        default=lambda self: self.env["purchase.type"].search(
            [("is_default", "=", True)], limit=1
        ),
    )
    procurement_method_id = fields.Many2one(
        comodel_name="procurement.method",
        string="Procurement Method",
        ondelete="restrict",
        index=True,
    )
    to_create = fields.Selection(
        related="purchase_type_id.to_create",
    )
    procurement_method_ids = fields.Many2many(
        related="purchase_type_id.procurement_method_ids",
    )
    expense_reason = fields.Text(
        string="Reason",
    )
    procurement_committee_ids = fields.One2many(
        comodel_name="procurement.committee",
        inverse_name="request_id",
        string="Procurement Committees",
        domain=[("committee_type", "=", "procurement")],
        copy=True,
    )
    work_acceptance_committee_ids = fields.One2many(
        comodel_name="procurement.committee",
        inverse_name="request_id",
        string="Work Acceptance Committees",
        domain=[("committee_type", "=", "work_acceptance")],
        copy=True,
    )
    assigned_to = fields.Many2one(
        string="Purchase Representative",
        copy=False,
    )
    verified_by = fields.Many2one(
        comodel_name="res.users",
        string="Verified By",
        index=True,
        copy=False,
        tracking=True,
    )
    approved_by = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        index=True,
        copy=False,
        tracking=True,
    )
    date_verified = fields.Date(
        string="Verified Date",
        copy=False,
    )
    date_approved = fields.Date(
        string="Approved Date",
        copy=False,
    )
    substate_sequence = fields.Integer(related="substate_id.sequence")

    def action_to_substate(self):
        self.ensure_one()
        sequence = self.env.context.get("to_substate_sequence", 0)
        substate = self.env["base.substate"].search(
            [("model", "=", "purchase.request"), ("sequence", "=", sequence)], limit=1
        )
        self.write(
            {
                "substate_id": substate.id,
                "verified_by": self.env.user.id,
                "date_verified": fields.Date.today(),
            }
        )

    @api.onchange("purchase_type_id")
    def _onchange_purchase_type_id(self):
        procurement_methods = self.purchase_type_id.procurement_method_ids
        self.update(
            {
                "procurement_method_id": len(procurement_methods) == 1
                and procurement_methods.id
                or False,
            }
        )

    def button_approved(self):
        self.write(
            {"approved_by": self.env.user.id, "date_approved": fields.Date.today()}
        )
        return super().button_approved()
