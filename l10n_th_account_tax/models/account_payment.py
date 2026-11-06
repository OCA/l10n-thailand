# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    wht_cert_ids = fields.One2many(related="move_id.wht_cert_ids")
    has_wht = fields.Boolean(related="move_id.has_wht")
    wht_cert_status = fields.Selection(related="move_id.wht_cert_status")
    wht_certs_count = fields.Integer(
        string="# Withholding Tax Certs",
        compute="_compute_wht_certs_count",
    )
    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice",
        inverse_name="payment_id",
        copy=False,
        domain=[("reversing_id", "=", False), ("reversed_id", "=", False)],
    )
    tax_invoice_move_ids = fields.Many2many(
        comodel_name="account.move",
        string="Tax Invoice's Journal Entry",
        compute="_compute_tax_invoice_move_ids",
    )
    to_clear_tax = fields.Boolean(
        compute="_compute_tax_invoice_move_ids",
        help="Undue VAT entries waiting for the vendor's tax invoice",
    )

    @api.depends("wht_cert_ids")
    def _compute_wht_certs_count(self):
        for payment in self:
            payment.wht_certs_count = len(payment.wht_cert_ids)

    def button_wht_certs(self):
        return self.move_id.button_wht_certs()

    def action_create_wht_cert(self):
        self.ensure_one()
        return self.move_id.action_create_wht_cert()

    @api.depends("tax_invoice_ids.move_id.state")
    def _compute_tax_invoice_move_ids(self):
        for payment in self:
            moves = payment.tax_invoice_ids.move_id
            payment.tax_invoice_move_ids = moves
            payment.to_clear_tax = any(move.state == "draft" for move in moves)

    def open_clear_tax(self):
        """Open Wizard for clear tax with accounting date"""
        self.ensure_one()
        self._check_clear_tax()
        return {
            "name": self.env._("Clear Tax"),
            "type": "ir.actions.act_window",
            "res_model": "clear.tax",
            "view_mode": "form",
            "target": "new",
            "context": {"default_payment_id": self.id},
        }

    def _check_clear_tax(self):
        missing = self.tax_invoice_ids.filtered(
            lambda tinv: (
                tinv.move_id.state == "draft" and tinv._is_missing_vendor_info()
            )
        )
        if missing:
            missing[0]._raise_missing_vendor_info()

    def clear_tax_cash_basis(self, date=None):
        """Post the undue VAT entries waiting for the tax invoice"""
        self._check_clear_tax()
        moves = self.tax_invoice_move_ids.filtered(lambda move: move.state == "draft")
        if date:
            moves.write({"date": date})
        moves.action_post()
        return True

    def button_open_journal_entry(self):
        """Add undue VAT entries when open journal entry"""
        self.ensure_one()
        if not self.tax_invoice_move_ids:
            return super().button_open_journal_entry()
        moves = self.tax_invoice_move_ids + self.move_id
        return {
            "name": self.env._("Journal Entry"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context": {"create": False},
            "view_mode": "list,form",
            "domain": [("id", "in", moves.ids)],
        }
