# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseGuarantee(models.Model):
    _name = "purchase.guarantee"
    _description = "Purchase Guarantee"
    _inherit = ["mail.thread", "mail.activity.mixin", "analytic.mixin"]
    _order = "name desc"

    name = fields.Char(
        string="Guarantee Number",
        default="/",
    )
    reference = fields.Reference(
        selection=[
            ("purchase.requisition", "Purchase Agreement"),
            ("purchase.order", "Purchase Order"),
        ],
    )
    reference_model = fields.Char(
        compute="_compute_reference",
        store=True,
    )
    requisition_id = fields.Many2one(
        comodel_name="purchase.requisition",
        compute="_compute_reference",
        string="Purchase Requisition",
        index=True,
        store=True,
        ondelete="restrict",
    )
    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        compute="_compute_reference",
        string="Purchase Order",
        index=True,
        store=True,
        ondelete="restrict",
    )
    guarantee_method_id = fields.Many2one(
        comodel_name="purchase.guarantee.method",
        index=True,
        ondelete="restrict",
        compute="_compute_guarantee_method_id",
        store=True,
        readonly=False,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        index=True,
        ondelete="restrict",
        compute="_compute_partner_id",
        store=True,
        readonly=False,
    )
    guarantee_type_id = fields.Many2one(
        comodel_name="purchase.guarantee.type",
        index=True,
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True,
    )
    amount = fields.Monetary(
        currency_field="currency_id",
        default=0.0,
    )
    date_guarantee_receive = fields.Date(
        string="Guarantee Receive Date",
    )
    analytic_distribution = fields.Json(
        compute="_compute_analytic",
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic Tags",
        compute="_compute_analytic",
        store=True,
        readonly=False,
    )
    invoice_ids = fields.Many2many(
        comodel_name="account.move",
        relation="account_move_guarantee_rel",
        column1="guarantee_id",
        column2="move_id",
        string="Invoice Ref",
    )
    amount_received = fields.Monetary(
        string="Received",
        currency_field="currency_id",
        compute="_compute_amount_received",
    )
    document_ref = fields.Char()
    date_return = fields.Date(
        string="Return Date",
    )
    bill_ids = fields.Many2many(
        comodel_name="account.move",
        relation="account_move_return_guarantee_rel",
        column1="guarantee_id",
        column2="move_id",
        string="Bill Ref",
    )
    amount_returned = fields.Monetary(
        string="Returned",
        currency_field="currency_id",
        compute="_compute_amount_returned",
    )
    date_due_guarantee = fields.Date(
        string="Guarantee Due Date",
    )
    note = fields.Text()
    can_edit_guarantee_method = fields.Boolean(
        compute="_compute_can_edit_guarantee_method",
    )
    active = fields.Boolean(default=True)

    @api.depends("reference_model")
    def _compute_can_edit_guarantee_method(self):
        for rec in self:
            rec.can_edit_guarantee_method = False
            guarantee_method = self.env["purchase.guarantee.method"].search(
                [("default_for_model", "=", rec.reference_model)]
            )
            if len(guarantee_method) > 1:
                rec.can_edit_guarantee_method = True

    @api.depends("reference")
    def _compute_reference(self):
        for rec in self.filtered("reference"):
            if rec.reference._name == "purchase.requisition":
                rec.requisition_id = rec.reference
                rec.reference_model = rec.reference._name
            elif rec.reference._name == "purchase.order":
                rec.purchase_id = rec.reference
                if rec.reference.state in ["draft", "sent"]:
                    rec.reference_model = f"{rec.reference._name}.rfq"
                elif rec.reference.state in ["purchase"]:
                    rec.reference_model = f"{rec.reference._name}.po"
            rec._check_reference_status()

    def _check_reference_status(self):
        self.ensure_one()
        states = []
        if self.reference._name == "purchase.requisition":
            states.append("confirmed")
        elif self.reference._name == "purchase.order":
            states.extend(["draft", "sent", "purchase"])

        if states and self.reference.state not in states:
            ref = dict(self._fields["reference"].selection).get(self.reference._name)
            state = ", ".join(
                [
                    dict(self.reference._fields["state"].selection).get(state)
                    for state in states
                ]
            )
            raise UserError(self.env._(f"{ref} must be in status: {state}"))

    @api.depends("reference")
    def _compute_guarantee_method_id(self):
        GuaranteeMethod = self.env["purchase.guarantee.method"]
        for rec in self.filtered("reference"):
            dom = []
            if rec.reference._name == "purchase.requisition":
                dom = [("default_for_model", "=", rec.reference._name)]
            elif rec.reference._name == "purchase.order":
                if rec.reference.state in ["draft", "sent"]:
                    dom = [
                        (
                            "default_for_model",
                            "=",
                            "{}.{}".format(rec.reference._name, "rfq"),
                        )
                    ]
                elif rec.reference.state in ["purchase"]:
                    dom = [
                        (
                            "default_for_model",
                            "=",
                            "{}.{}".format(rec.reference._name, "po"),
                        )
                    ]
            rec.guarantee_method_id = GuaranteeMethod.search(dom)[:1]

    @api.depends("purchase_id")
    def _compute_partner_id(self):
        for rec in self.filtered("purchase_id"):
            rec.partner_id = rec.purchase_id.partner_id.id

    @api.depends("reference")
    def _compute_analytic(self):
        for rec in self:
            origin = False
            if rec.reference:
                if rec.reference._name == "purchase.requisition":
                    origin = rec.reference.line_ids
                elif rec.reference._name == "purchase.order":
                    origin = rec.reference.order_line
            analytics = origin and origin.analytic_distribution or False
            rec.analytic_tag_ids = origin and origin.mapped("analytic_tag_ids") or []
            if analytics:
                rec.analytic_distribution = analytics

    @api.depends("invoice_ids")
    def _compute_amount_received(self):
        for rec in self:
            rec.amount_received = sum(rec.invoice_ids.mapped("amount_total")) - sum(
                rec.invoice_ids.mapped("amount_residual")
            )

    @api.depends("bill_ids")
    def _compute_amount_returned(self):
        for rec in self:
            rec.amount_returned = sum(rec.bill_ids.mapped("amount_total")) - sum(
                rec.bill_ids.mapped("amount_residual")
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "purchase.guarantee"
                )
        return super().create(vals)

    @api.depends("reference", "name")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for rec in self:
            if rec.reference:
                rec.display_name = f"{rec.name} ({rec.reference.name})"
        return res
