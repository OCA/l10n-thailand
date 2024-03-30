# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountPaymentRegisterOrder(models.Model):
    _name = "account.payment.register.order"
    _inherit = ["account.payment.register", "mail.thread"]
    _description = "Payment Register Order Model"
    _order = "id desc"
    _transient = False

    name = fields.Char(
        required=True,
        default="/",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submit", "Submit"),
            ("paid", "Paid"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        readonly=True,
    )
    line_ids = fields.Many2many(
        "account.move.line",
        "account_payment_register_order_move_line_rel",
        "register_id",
        "line_id",
        string="Journal items",
        readonly=True,
        copy=False,
    )
    payment_ids = fields.Many2many(
        "account.payment",
        "account_payment_register_order_payment_rel",
        "register_id",
        "payment_id",
        string="Payments",
        readonly=True,
        copy=False,
    )
    deduction_ids = fields.One2many(
        comodel_name="account.payment.deduction.order",
        inverse_name="payment_id",
        string="Deductions",
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )

    def _get_payment_number(self):
        self.ensure_one()
        # payment_type is either inbound or outbound
        code = "account.payment.register.order.%s" % self.payment_type
        self = self.with_context(ir_sequence_date=self.payment_date)
        number = self.env["ir.sequence"].next_by_code(code) or "/"
        return number

    def action_submit(self):
        for rec in self.filtered(lambda x: not x.name or x.name == "/"):
            rec._check_constraint_create_payment()
            rec.write({"name": rec._get_payment_number()})
        self.write({"state": "submit"})

    def action_draft(self):
        if self.filtered("payment_ids"):
            raise UserError(_("Cannot set to draft if payment(s) was created"))
        self.write({"state": "draft"})

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

    def _check_constraint_create_payment(self):
        self.ensure_one()
        prec_digits = self.company_id.currency_id.decimal_places
        amount_residual = sum(self.line_ids.mapped("amount_residual"))
        if (
            float_compare(
                amount_residual,
                self.amount,
                precision_digits=prec_digits,
            )
            == -1
        ):
            raise UserError(
                _(
                    "Total amount residual must be less than or equal to %(amount_residual)s"
                )
                % {"amount_residual": amount_residual}
            )

    def action_create_payments(self):
        self.ensure_one()
        self._check_constraint_create_payment()
        self = self.with_context(dont_redirect_to_payments=False)
        self.write({"state": "paid"})
        res = super().action_create_payments()
        if res.get("domain"):
            self.payment_ids = res["domain"][0][2]
        else:
            self.payment_ids = [res["res_id"]]
        # Ref to this payment register
        for payment in self.payment_ids:
            payment.ref += " %s" % self.name
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
