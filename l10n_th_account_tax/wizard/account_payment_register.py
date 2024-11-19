# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Withholding Tax",
        check_company=True,
        help="Optional hidden field to keep wht_tax. Useful for case 1 tax only",
    )
    wht_amount_base = fields.Monetary(
        string="Withholding Base",
        compute="_compute_wht_amount",
        store=True,
        readonly=False,
        help="Based amount for the tax amount",
    )

    @api.depends("early_payment_discount_mode")
    def _compute_payment_difference_handling(self):
        res = super()._compute_payment_difference_handling()
        for wizard in self:
            if (
                wizard.wht_amount_base
                and wizard.wht_tax_id
                and wizard.payment_difference
            ):
                wizard.payment_difference_handling = "reconcile"
        return res

    @api.depends("wht_tax_id", "wht_amount_base")
    def _compute_wht_amount(self):
        for rec in self:
            if rec.wht_tax_id and rec.wht_amount_base:
                if rec.wht_tax_id.is_pit:
                    rec._onchange_pit()
                else:
                    rec._onchange_wht()

    def _onchange_wht(self):
        """Onchange set for normal withholding tax"""
        amount_wht = (self.wht_tax_id.amount / 100) * self.wht_amount_base
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
        amount_base_company = self.currency_id._convert(
            self.wht_amount_base,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        amount_pit_company = self.wht_tax_id.pit_id._compute_expected_wht(
            self.partner_id,
            amount_base_company,
            self.payment_date,
            self.company_id.currency_id,
            self.company_id,
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

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        # Check case auto and manual withholding tax
        if self.payment_difference_handling == "reconcile" and self.wht_tax_id:
            payment_vals["write_off_line_vals"] = self._prepare_writeoff_move_line(
                payment_vals.get("write_off_line_vals", [])
            )
        return payment_vals

    @api.depends(
        "can_edit_wizard",
        "source_amount",
        "source_amount_currency",
        "source_currency_id",
        "company_id",
        "currency_id",
        "payment_date",
        "installments_mode",
    )
    def _compute_amount(self):
        """This function is the first entry point, to calculate withholding amount"""
        res = super()._compute_amount()
        # Get the sum withholding tax amount from invoice line
        skip_wht_deduct = self.env.context.get("skip_wht_deduct")
        active_model = self.env.context.get("active_model")
        if not skip_wht_deduct and active_model == "account.move.line":
            active_ids = self.env.context.get("active_ids", [])
            inv_lines = self.env["account.move.line"].browse(active_ids)
            wht_move_lines = inv_lines.filtered("wht_tax_id")
            if not wht_move_lines:
                return res
            # Case WHT only, ensure only 1 wizard
            self.ensure_one()
            deduction_list, _ = wht_move_lines._prepare_deduction_list(
                self.payment_date, self.currency_id
            )
            # Support only case single WHT line in this module
            # Use `l10n_th_account_tax_multi` if there are mixed lines
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
        wht_tax = wht_move_lines.mapped("wht_tax_id")
        if wht_tax and len(wht_tax) == 1:
            self.wht_tax_id = wht_tax
            self.writeoff_account_id = self.wht_tax_id.account_id
            self.writeoff_label = self.wht_tax_id.display_name
        return True

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "account.move.line":
            active_ids = self.env.context.get("active_ids", False)
            move_ids = (
                self.env["account.move.line"].browse(active_ids).mapped("move_id")
            )
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

    @api.onchange("currency_id")
    def _onchange_currency_id(self):
        """Change currency in wizard, Withholding Base should be updated"""
        res = super()._onchange_currency_id()
        if self.custom_user_amount:
            self.wht_amount_base = self.amount + self.payment_difference
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
        return super()._create_payments()

    def _prepare_writeoff_move_line(self, write_off_line_vals):
        """Prepare value withholding tax move of payment"""
        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            self.currency_id,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        wht_amount_base_company = self.company_id.currency_id.round(
            self.wht_amount_base * conversion_rate
        )
        for write_off in write_off_line_vals:
            write_off["wht_tax_id"] = self.wht_tax_id.id
            write_off["tax_base_amount"] = wht_amount_base_company
        return write_off_line_vals

    def action_create_payments(self):
        # For case calculate tax invoice partial payment
        if self.payment_difference_handling == "open":
            self = self.with_context(partial_payment=True)
        elif self.payment_difference_handling == "reconcile":
            self = self.with_context(skip_account_move_synchronization=True)
        # Find original moves
        model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids", False)
        moves = self.env[model].browse(active_ids)
        if model == "account.move.line":
            moves = moves.mapped("move_id")
        # Add context reverse_tax_invoice for case reversal
        if any(move.move_type in ["in_refund", "out_refund"] for move in moves):
            self = self.with_context(reverse_tax_invoice=True)
        return super().action_create_payments()
