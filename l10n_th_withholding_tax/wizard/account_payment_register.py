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

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        # Check case auto and manual withholding tax
        if self.payment_difference_handling == "reconcile" and self.wt_tax_id:
            payment_vals.update({"wt_tax_id": self.wt_tax_id.id})
        return payment_vals

    def _update_payment_register(self, amount_wt, inv_lines):
        self.ensure_one()
        self.amount -= amount_wt
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
            amount_wt = 0
            for line in move_lines:
                base_amount = line._get_wt_base_amount()
                amount_wt += line.wt_tax_id.amount / 100 * base_amount
            if amount_wt:
                self._update_payment_register(amount_wt, move_lines)
        return res

    @api.model
    def default_get(self, fields_list):
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", False)
            move_ids = self.env["account.move"].browse(active_ids)
            wt_tax_line = move_ids.line_ids.filtered(lambda l: l.wt_tax_id)
            if len(move_ids) > 1 and wt_tax_line:
                raise UserError(
                    _(
                        "You can't register a payment on tree view "
                        "because there is withholding tax in line."
                    )
                )
        return super().default_get(fields_list)
