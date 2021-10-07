# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


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
            if self.wt_tax_id.is_pit:
                self._onchange_pit()
            else:
                self._onchange_wht()

    def _onchange_wht(self):
        """ Onchange set for normal withholding tax """
        amount_wt = self.wt_tax_id.amount / 100 * self.wt_amount_base
        amount_currency = self.company_id.currency_id._convert(
            self.source_amount,
            self.currency_id,
            self.company_id,
            self.payment_date,
        )
        self.amount = amount_currency - amount_wt
        self.writeoff_account_id = self.wt_tax_id.account_id
        self.writeoff_label = self.wt_tax_id.display_name

    def _onchange_pit(self):
        """ Onchange set for personal income tax """
        if not self.wt_tax_id.pit_id:
            raise UserError(
                _("No effective PIT rate for date %s")
                % format_date(self.env, self.payment_date)
            )
        amount_base_company = self.currency_id._convert(
            self.wt_amount_base,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        amount_pit_company = self.wt_tax_id.pit_id._compute_expected_wt(
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
        self.writeoff_account_id = self.wt_tax_id.account_id
        self.writeoff_label = self.wt_tax_id.display_name

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        # Check case auto and manual withholding tax
        if self.payment_difference_handling == "reconcile" and self.wt_tax_id:
            payment_vals.update({"wt_tax_id": self.wt_tax_id.id})
        return payment_vals

    def _update_payment_register(self, amount_base, amount_wt, wt_move_lines):
        self.ensure_one()
        if not amount_base:
            return False
        self.amount -= amount_wt
        self.wt_amount_base = amount_base
        self.payment_difference_handling = "reconcile"
        wt_tax = wt_move_lines.mapped("wt_tax_id")
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
            wt_move_lines = invoices.mapped("line_ids").filtered("wt_tax_id")
            if not wt_move_lines:
                return res
            # Case WHT only, ensure only 1 wizard
            self.ensure_one()
            amount_base, amount_wt = wt_move_lines._get_wt_amount(
                self.currency_id, self.payment_date
            )
            self._update_payment_register(amount_base, amount_wt, wt_move_lines)
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
        payments = super()._create_payments()
        # Create account.withholding.move from table multi deduction
        if (
            self.payment_difference_handling == "reconcile"
            and self.group_payment
            and self.wt_tax_id
        ):
            vals = self._prepare_withholding_move(
                self.partner_id,
                self.payment_date,
                self.wt_tax_id,
                self.wt_amount_base,
                self.payment_difference,
                self.currency_id,
                self.company_id,
            )
            payments[0].write({"wht_move_ids": [(0, 0, vals)]})
        return payments

    def _prepare_withholding_move(
        self, partner, date, wt_tax, base, amount, currency, company
    ):
        amount_income = currency._convert(base, company.currency_id, company, date)
        amount_wt = currency._convert(amount, company.currency_id, company, date)
        return {
            "partner_id": partner.id,
            "amount_income": amount_income,
            "wt_tax_id": wt_tax.id,
            "amount_wt": amount_wt,
        }
