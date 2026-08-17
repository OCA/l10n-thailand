# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    to_clear_tax = fields.Boolean(
        default=False,
        copy=False,
        help="When defer journal entry posting, this will show button",
    )
    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice",
        inverse_name="payment_id",
        copy=False,
        domain=[("reversing_id", "=", False), ("reversed_id", "=", False)],
    )
    tax_invoice_move_ids = fields.Many2many(
        comodel_name="account.move",
        relation="payment_tax_invoice_rel",
        column1="payment_id",
        column2="tax_invoice_id",
        string="Tax Invoice's Journal Entry",
        compute="_compute_tax_invoice_move_ids",
    )
    wht_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="payment_id",
        string="Withholding",
        copy=False,
        help="All withholding moves, including non-PIT",
    )
    pit_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="payment_id",
        string="Personal Income Tax",
        domain=[("is_pit", "=", True)],
        copy=False,
    )
    wht_cert_status = fields.Selection(
        selection=[
            ("none", "Not yet created"),
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        compute="_compute_wht_cert_status",
    )
    has_wht = fields.Boolean(
        compute="_compute_has_wht",
    )

    wht_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="payment_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )
    wht_certs_count = fields.Integer(
        string="# Withholding Tax Certs",
        compute="_compute_wht_certs_count",
    )

    def _compute_has_wht(self):
        """Has WHT when
        1. Has wht_tax_id
        2. payment is not received (sale type)
        """
        for rec in self:
            wht_tax = bool(rec.move_id.line_ids.filtered("wht_tax_id"))
            not_inv = rec.payment_type != "inbound"
            rec.has_wht = wht_tax and not_inv

    @api.depends("wht_cert_ids.state")
    def _compute_wht_cert_status(self):
        for rec in self:
            rec.wht_cert_status = False
            if not rec.has_wht:
                continue
            if not rec.wht_cert_ids:
                rec.wht_cert_status = "none"
            elif "draft" in rec.wht_cert_ids.mapped("state"):
                rec.wht_cert_status = "draft"
            elif rec.wht_cert_ids.mapped("state") == ["done"]:
                rec.wht_cert_status = "done"
            elif rec.wht_cert_ids.mapped("state") == ["cancel"]:
                rec.wht_cert_status = "cancel"

    @api.depends("wht_cert_ids")
    def _compute_wht_certs_count(self):
        for payment in self:
            payment.wht_certs_count = len(payment.wht_cert_ids)

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_th_account_tax.action_withholding_tax_cert_menu"
        )
        action["domain"] = [("id", "in", self.wht_cert_ids.ids)]
        return action

    def open_clear_tax(self):
        """Open Wizard for clear tax with accounting date"""
        for payment in self:
            for tax_invoice in payment.tax_invoice_ids:
                if (
                    not tax_invoice.tax_invoice_number
                    or not tax_invoice.tax_invoice_date
                ):
                    raise UserError(
                        self.env._("Please fill in tax invoice and tax date")
                    )
        return {
            "name": "Clear Tax",
            "type": "ir.actions.act_window",
            "res_model": "clear.tax",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_payment_id": self.id,
            },
        }

    def clear_tax_cash_basis(self):
        for payment in self:
            payment.write({"to_clear_tax": False})
            moves = payment.tax_invoice_ids.mapped("move_id")
            payment_tax_ml = payment.tax_invoice_ids.mapped("move_line_id").ids
            for move in moves:
                if move.state != "draft":
                    continue
                move.action_post()
                # Reconcile Case Basis
                line = move.line_ids.filtered(
                    lambda ml, payment_tax_ml=payment_tax_ml: ml.id
                    not in payment_tax_ml
                )
                if line.account_id.reconcile:
                    origin_ml = move.tax_cash_basis_origin_move_id.line_ids
                    counterpart_line = origin_ml.filtered(
                        lambda ml, line=line: ml.account_id.id == line.account_id.id
                    )
                    (line + counterpart_line).reconcile()
        return True

    @api.depends("tax_invoice_ids")
    def _compute_tax_invoice_move_ids(self):
        for payment in self:
            payment.tax_invoice_move_ids = payment.tax_invoice_ids.mapped("move_id")

    def button_open_journal_entry(self):
        """Add tax cash basis when open journal entry"""
        self.ensure_one()
        if self.tax_invoice_move_ids:
            moves = self.tax_invoice_move_ids + self.move_id
            return {
                "name": self.env._("Journal Entry"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "context": {"create": False},
                "view_mode": "list,form",
                "domain": [("id", "in", moves.ids)],
            }
        return super().button_open_journal_entry()

    def create_wht_cert(self):
        self.ensure_one()
        self.move_id.create_wht_cert()
