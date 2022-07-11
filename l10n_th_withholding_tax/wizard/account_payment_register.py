# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Withholding Tax",
        help="Optional hidden field to keep wt_tax. Useful for case 1 tax only",
    )
    wt_amount_base = fields.Monetary(
        string="Withholding Base",
        help="Based amount for the tax amount",
    )

    @api.onchange("wt_tax_id", "wt_amount_base")
    def _onchange_wt_tax_id(self):
        if self.wt_tax_id and self.wt_amount_base:
            amount_wt = self.wt_tax_id.amount / 100 * self.wt_amount_base
            self.amount = self.source_amount_currency - amount_wt
            self.writeoff_account_id = self.wt_tax_id.account_id
            self.writeoff_label = self.wt_tax_id.display_name

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        # Check case auto and manual withholding tax
        if self.payment_difference_handling == "reconcile" and self.wt_tax_id:
            payment_vals.update({"wt_tax_id": self.wt_tax_id.id})
        return payment_vals

    def _update_payment_register(self, amount_base, amount_wt, inv_lines):
        self.ensure_one()
        self.amount -= amount_wt
        self.wt_amount_base = amount_base
        self.payment_difference_handling = "reconcile"
        wt_tax = inv_lines.mapped("wt_tax_id")
        if wt_tax and len(wt_tax) == 1:
            self.wt_tax_id = wt_tax
            self.writeoff_account_id = self.wt_tax_id.account_id
            self.writeoff_label = self.wt_tax_id.display_name
        return True

    @api.depends(
        "source_amount",
        "source_amount_currency",
        "source_currency_id",
        "company_id",
        "currency_id",
        "payment_date",
    )
    def _compute_amount(self):
        res = super()._compute_amount()
        # Get the sum withholding tax amount from invoice line
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            move_lines = invoices.mapped("line_ids").filtered("wt_tax_id")
            if not move_lines:
                return res
            # Case WHT only, ensure only 1 wizard
            self.ensure_one()
            amount_base, amount_wt = move_lines._get_wt_amount(
                self.currency_id, self.payment_date
            )
            if amount_wt:
                self._update_payment_register(amount_base, amount_wt, move_lines)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", False)
            move_ids = self.env["account.move"].browse(active_ids)
            partner_ids = move_ids.mapped("partner_id")
            wt_tax_line = move_ids.line_ids.filtered("wt_tax_id")
            if len(partner_ids) > 1 and wt_tax_line:
                raise UserError(
                    _(
                        "You can't register a payment for invoices "
                        "(with withholding tax) belong to multiple partners."
                    )
                )
            res["group_payment"] = True
        return res

    def _create_payments(self):
        self.ensure_one()
        if self.wt_tax_id and not self.group_payment:
            raise UserError(
                _(
                    "Please check Group Payments when dealing "
                    "with multiple invoices that has withholding tax."
                )
            )
        return super()._create_payments()
