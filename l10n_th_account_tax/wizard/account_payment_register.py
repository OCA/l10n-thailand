# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Withholding Tax",
        help="Optional hidden field to keep wht_tax. Useful for case 1 tax only",
    )
    wht_amount_base = fields.Monetary(
        string="Withholding Base",
        help="Based amount for the tax amount",
    )

    @api.onchange("wht_tax_id", "wht_amount_base")
    def _onchange_wht_tax_id(self):
        if self.wht_tax_id and self.wht_amount_base:
            if self.wht_tax_id.is_pit:
                self._onchange_pit()
            else:
                self._onchange_wht()

    def _onchange_wht(self):
        """Onchange set for normal withholding tax"""
        amount_wht = self.wht_tax_id.amount / 100 * self.wht_amount_base
        amount_currency = self.company_id.currency_id._convert(
            self.source_amount,
            self.currency_id,
            self.company_id,
            self.payment_date,
        )
        self.amount = amount_currency - amount_wht
        self.writeoff_account_id = self.wht_tax_id.account_id
        self.writeoff_label = self.wht_tax_id.display_name

    def _onchange_pit(self):
        """Onchange set for personal income tax"""
        if not self.wht_tax_id.pit_id:
            raise UserError(
                _("No effective PIT rate for date %s")
                % format_date(self.env, self.payment_date)
            )
        amount_base_company = self.currency_id._convert(
            self.wht_amount_base,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        amount_pit_company = self.wht_tax_id.pit_id._compute_expected_wht(
            self.partner_id,
            amount_base_company,
            pit_date=self.payment_date,
            currency=self.company_id.currency_id,
            company=self.company_id,
        )
        amount_pit = self.company_id.currency_id._convert(
            amount_pit_company,
            self.currency_id,
            self.company_id,
            self.payment_date,
        )
        amount_currency = self.company_id.currency_id._convert(
            self.source_amount,
            self.currency_id,
            self.company_id,
            self.payment_date,
        )
        self.amount = amount_currency - amount_pit
        self.writeoff_account_id = self.wht_tax_id.account_id
        self.writeoff_label = self.wht_tax_id.display_name

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        # Check case auto and manual withholding tax
        if self.payment_difference_handling == "reconcile" and self.wht_tax_id:
            payment_vals["write_off_line_vals"] = self._prepare_writeoff_move_line(
                payment_vals.get("write_off_line_vals", False)
            )
        return payment_vals

    @api.depends(
        "source_amount",
        "source_amount_currency",
        "source_currency_id",
        "company_id",
        "currency_id",
        "payment_date",
    )
    def _compute_amount(self):
        """This function is the first entry point, to calculate withholding amount"""
        res = super()._compute_amount()
        # Get the sum withholding tax amount from invoice line
        skip_wht_deduct = self.env.context.get("skip_wht_deduct")
        active_model = self.env.context.get("active_model")
        if not skip_wht_deduct and active_model == "account.move":
            active_ids = self.env.context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            wht_move_lines = invoices.mapped("line_ids").filtered("wht_tax_id")
            if not wht_move_lines:
                return res
            # Case WHT only, ensure only 1 wizard
            self.ensure_one()
            deduction_list, _ = wht_move_lines._prepare_deduction_list(
                currency=self.currency_id, date=self.payment_date
            )
            # Support only case single WHT line in this module
            # Use l10n_th_account_tax_mult if there are mixed lines
            amount_base = 0
            amount_wht = 0
            if len(deduction_list) == 1:
                amount_base = deduction_list[0]["wht_amount_base"]
                amount_wht = deduction_list[0]["amount"]
            self._update_payment_register(amount_base, amount_wht, wht_move_lines)
        return res

    def _update_payment_register(self, amount_base, amount_wht, wht_move_lines):
        self.ensure_one()
        if not amount_base:
            return False
        self.amount -= amount_wht
        self.wht_amount_base = amount_base
        self.payment_difference_handling = "reconcile"
        wht_tax = wht_move_lines.mapped("wht_tax_id")
        if wht_tax and len(wht_tax) == 1:
            self.wht_tax_id = wht_tax
            self.writeoff_account_id = self.wht_tax_id.account_id
            self.writeoff_label = self.wht_tax_id.display_name
        return True

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "account.move":
            active_ids = self.env.context.get("active_ids", False)
            move_ids = self.env["account.move"].browse(active_ids)
            partner_ids = move_ids.mapped("partner_id")
            wht_tax_line = move_ids.line_ids.filtered("wht_tax_id")
            if len(partner_ids) > 1 and wht_tax_line:
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
        if self.wht_tax_id and not self.group_payment:
            raise UserError(
                _(
                    "Please check Group Payments when dealing "
                    "with multiple invoices that has withholding tax."
                )
            )
        payments = super()._create_payments()
        return payments

    def _prepare_writeoff_move_line(self, write_off_line_vals=None):
        write_off_line_vals = write_off_line_vals or {}
        if write_off_line_vals:
            write_off_line_vals["wht_tax_id"] = self.wht_tax_id.id
            write_off_line_vals["wht_amount_base"] = self.wht_amount_base
            return write_off_line_vals
        return {
            "name": self.writeoff_label,
            "amount": self.payment_difference,
            "wht_tax_id": self.wht_tax_id.id,
            "wht_amount_base": self.wht_amount_base,
            "account_id": self.writeoff_account_id.id,
        }

    def action_create_payments(self):
        # For case calculate tax invoice partial payment
        if self.payment_difference_handling == "open":
            self = self.with_context(partial_payment=True)
        elif self.payment_difference_handling == "reconcile":
            self = self.with_context(skip_account_move_synchronization=True)
        return super().action_create_payments()
