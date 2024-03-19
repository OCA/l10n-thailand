# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegisterPerm(models.Model):
    _name = "account.payment.register.perm"
    _inherit = ["account.payment.register", "mail.thread"]
    _description = "Payment Register Permanemt Model"
    _order = "id desc"

    name = fields.Char(
        required=True,
        default="/",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("paid", "Paid"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        readonly=True,
    )
    line_ids = fields.Many2many(
        "account.move.line",
        "account_payment_register_perm_move_line_rel",
        "register_id",
        "line_id",
        string="Journal items",
        readonly=True,
        copy=False,
    )
    payment_ids = fields.Many2many(
        "account.payment",
        "account_payment_register_perm_payment_rel",
        "register_id",
        "payment_id",
        string="Payments",
        readonly=True,
        copy=False,
    )
    deduction_ids = fields.One2many(
        comodel_name="account.payment.deduction.perm",
        inverse_name="payment_id",
        string="Deductions",
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )

    def _get_default_name(self, vals):
        return (
            self.env["ir.sequence"].next_by_code("account.payment.register.perm") or "/"
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self._get_default_name(vals)
        return super().create(vals_list)

    def action_cancel(self):
        self.write({"state": "cancel"})
        self.payment_ids.action_draft()

    def action_reconcile_invoice_payment(self):
        self.ensure_one()
        if not self.payment_ids or not self.line_ids:
            raise UserError(_("Cannot reconcile, not valid invoice or payment"))
        if self.payment_ids.filtered(lambda l: l.state != "draft"):
            raise UserError(_("To reconcile, payment(s) should be in draft state"))
        if self.line_ids.filtered(
            lambda l: l.parent_state != "posted" or l.move_id.payment_state == "paid"
        ):
            raise UserError(_("To reconcile, invoice(s) should be posted but not paid"))
        self.payment_ids.action_post()
        domain = [
            ("parent_state", "=", "posted"),
            ("account_type", "in", ("asset_receivable", "liability_payable")),
            ("reconciled", "=", False),
        ]
        payment_lines = self.payment_ids.line_ids.filtered_domain(domain)
        lines = self.line_ids
        for account in payment_lines.account_id:
            (payment_lines + lines).filtered_domain(
                [("account_id", "=", account.id), ("reconciled", "=", False)]
            ).reconcile()
        self.write({"state": "paid"})

    def action_create_payments(self):
        self.ensure_one()
        self = self.with_context(dont_redirect_to_payments=False)
        self.write({"state": "paid"})
        res = super().action_create_payments()
        if res.get("domain"):
            self.payment_ids = res["domain"][0][2]
        else:
            self.payment_ids = [res["res_id"]]
        return True

    def open_invoices(self):
        self.ensure_one()
        action = {
            "name": _("Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", self.line_ids.move_id.ids)],
            "context": {"create": False},
        }
        return action

    def open_payments(self):
        self.ensure_one()
        action = {
            "name": _("Payments"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "list,form",
            "domain": [("id", "in", self.payment_ids.ids)],
            "context": {"create": False},
        }
        return action
