# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BankPaymentExportLine(models.Model):
    _name = "bank.payment.export.line"
    _inherit = "bank.payment.export.common"
    _description = "Bank Payment Export File"

    payment_export_id = fields.Many2one(
        comodel_name="bank.payment.export",
        index=True,
    )
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        required=True,
        domain=lambda self: self._domain_payment_id(),
        ondelete="restrict",
        index=True,
    )
    payment_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="payment_id.journal_id",
        string="Journal",
    )
    payment_partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="payment_id.partner_id",
        string="Vendor",
    )
    payment_partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank",
        compute="_compute_payment_default",
        store=True,
        string="Recipient Bank",
        index=True,
    )
    payment_bank_id = fields.Many2one(
        comodel_name="res.bank",
        related="payment_partner_bank_id.bank_id",
        string="Bank",
        store=True,
        index=True,
    )
    payment_date = fields.Date(related="payment_id.date")
    payment_amount = fields.Monetary(related="payment_id.amount")
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="payment_export_id.company_id",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="payment_export_id.currency_id",
        store=True,
    )
    state = fields.Selection(
        related="payment_export_id.state",
        string="Status",
        store=True,
    )

    _sql_constraints = [
        (
            "export_product_uniq",
            "unique(payment_export_id, payment_id)",
            "Duplicate payment in transaction not allowed!",
        )
    ]

    @api.depends("payment_id")
    def _compute_payment_default(self):
        for rec in self:
            rec.payment_partner_bank_id = rec.payment_id.partner_bank_id or False

    def _domain_payment_id(self):
        """Condition search all payment
        1. Currency same as company currency
        2. Company same as company_id
        3. Payment not exported and state 'paid' only
        4. Payment method must be 'Manual' on Vendor Payment
        5. Journal payment must be type 'Bank' only
        """
        method_manual_out = self.env.ref("account.account_payment_method_manual_out")
        domain = (
            f"[('export_status', '=', 'draft'), "
            f"('state', '=', 'paid'), "
            f"('payment_method_id', '=', {method_manual_out.id}), "
            f"('journal_id.type', '=', 'bank'), "
            f"('company_id', '=', company_id), "
            f"('currency_id', '=', currency_id)]"
        )
        return domain

    def clear_payment_exported(self):
        return self.mapped("payment_id").write(
            {
                "export_status": "draft",
                "payment_export_id": False,
            }
        )

    def _action_reject_bank_payment(self):
        return self.payment_export_id.action_reject()

    def action_reject(self):
        self.clear_payment_exported()
        self.write({"state": "reject"})
        lines_not_reject = self.payment_export_id.export_line_ids.filtered(
            lambda line: line.state != "reject"
        )
        # all line rejected, it should auto reject header too.
        if not lines_not_reject:
            self._action_reject_bank_payment()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        # Update export_status and payment_export_id in payment
        export_lines = super().create(vals_list)
        # NOTE: vals_list must same as value of payment_export_id only
        payment_export_id = vals_list[0]["payment_export_id"] if vals_list else None
        export_lines.mapped("payment_id").write(
            {
                "export_status": "to_export",
                "payment_export_id": payment_export_id,
            }
        )
        return export_lines

    def unlink(self):
        """Check state draft can delete only."""
        self.clear_payment_exported()
        return super().unlink()
