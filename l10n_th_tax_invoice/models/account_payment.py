# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, fields, models
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
    move_id = fields.Many2one(
        comodel_name="account.move", string="Journal Entry", compute="_compute_move_id",
    )
    tax_invoice_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Tax Invoice's Journal Entry",
        compute="_compute_tax_invoice_move_id",
    )

    def clear_tax_cash_basis(self):
        for payment in self:
            for tax_invoice in payment.tax_invoice_ids:
                if (
                    not tax_invoice.tax_invoice_number
                    or not tax_invoice.tax_invoice_date
                ):
                    raise UserError(_("Please fill in tax invoice and tax date"))
            payment.write({"to_clear_tax": False})
            moves = payment.tax_invoice_ids.mapped("move_id")
            for move in moves.filtered(lambda l: l.state == "draft"):
                move.ensure_one()
                move.post()
        return True

    def _compute_move_id(self):
        for payment in self:
            payment.move_id = payment.move_line_ids.mapped("move_id")[:1]

    def _compute_tax_invoice_move_id(self):
        for payment in self:
            payment.tax_invoice_move_id = payment.tax_invoice_ids.mapped("move_id")[:1]

    def button_journal_entries(self):
        res = super().button_journal_entries()
        res["domain"] = [
            ("move_id", "in", [self.move_id.id, self.tax_invoice_move_id.id])
        ]
        return res
