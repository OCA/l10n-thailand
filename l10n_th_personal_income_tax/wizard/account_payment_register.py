# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_th_withholding_tax_cert.models.withholding_tax_cert import (
    WHT_CERT_INCOME_TYPE,
)


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.onchange("group_payment")
    def _onchange_group_payment(self):
        """ Compute payment difference from tree view """
        model = self._context.get("active_model", False)
        if model == "account.move" and self.group_payment:
            self._compute_amount()

    def _create_payments(self):
        payments = super()._create_payments()
        for payment in payments:
            move_ids = payment.reconciled_bill_ids.filtered("account_pit")
            if move_ids and self.group_payment:
                # Multi-Currency
                amount_income_currency = sum(move_ids.mapped("amount_untaxed")) or 0.0
                amount_income = move_ids[0].currency_id._convert(
                    amount_income_currency,
                    self.company_id.currency_id,
                    self.company_id,
                    self.payment_date,
                )
                payment_difference = self.payment_difference
                if self.company_id.currency_id != self.currency_id:
                    payment_difference = self.currency_id._convert(
                        payment_difference,
                        self.company_id.currency_id,
                        self.company_id,
                        self.payment_date,
                    )
                payment.write(
                    {
                        "pit_line": [
                            (
                                0,
                                0,
                                {
                                    "partner_id": payment.partner_id.id,
                                    "wt_cert_income_type": move_ids[
                                        0
                                    ].pit_wt_cert_income_type
                                    or False,
                                    "amount_income": amount_income,
                                    "amount_wt": payment_difference,
                                },
                            )
                        ],
                    }
                )
        return payments

    def _get_pit_amount_yearly(self, partner_id, date=False):
        if not date:
            date = fields.Date.context_today(self)
        calendar_year = date.strftime("%Y")
        pit_year = partner_id.pit_line.filtered(
            lambda l: l.calendar_year == calendar_year
        )
        return sum(pit_year.mapped("amount_income"))

    def _default_pit_wt_account_id(self, date=False):
        if not date:
            date = fields.Date.context_today(self)
        pit = self.env["personal.income.tax"].search(
            [("effective_date", "<=", date)], order="effective_date desc", limit=1
        )
        return pit.wt_account_id or False

    def _compute_expected_wt(self, move_ids, pit_date=False):
        PIT = self.env["personal.income.tax"]
        # Total previous amount personal income tax
        pit_amount_year = self._get_pit_amount_yearly(self.partner_id)
        # Multi-Currency: Convert other to main currency
        base_amount = move_ids[0].currency_id._convert(
            sum(move_ids.mapped("amount_untaxed")),
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )
        total_pit = pit_amount_year + base_amount
        expected_wt = PIT.calculate_rate_wt(total_pit, base_amount, date=pit_date)
        return expected_wt

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
        model = self._context.get("active_model", False)
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (
            len(batches[0]["lines"]) == 1 or self.group_payment
        )
        # Compute amount for case group payment, register payment on form view
        if model == "account.move" and edit_mode:
            move_ids = self.env[model].browse(self._context.get("active_ids", []))
            # Check there isn't account pit on account.move
            if not any(list(set(move_ids.mapped("account_pit")))):
                return res
            pit_date = self._context.get("pit_date", False)
            wt_account_id = self._default_pit_wt_account_id(date=pit_date)
            expected_wt = self._compute_expected_wt(move_ids, pit_date)
            if expected_wt:
                # Convert main to other currency for display amount difference
                company_currency = self.company_id.currency_id
                if company_currency != self.currency_id:
                    expected_wt = company_currency._convert(
                        expected_wt,
                        move_ids[0].currency_id,
                        self.company_id,
                        self.payment_date,
                    )
                list_writeoff_label = [
                    dict(WHT_CERT_INCOME_TYPE).get(move.pit_wt_cert_income_type, False)
                    for move in move_ids
                ]
                self.amount -= expected_wt
                self.payment_difference_handling = "reconcile"
                self.writeoff_account_id = wt_account_id and wt_account_id.id or False
                self.writeoff_label = (
                    any(list_writeoff_label)
                    and ", ".join(list_writeoff_label)
                    or self.writeoff_label
                )
        return res

    @api.model
    def default_get(self, fields_list):
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", False)
            move_ids = self.env["account.move"].browse(active_ids)
            if len(set(move_ids.mapped("account_pit"))) > 1:
                raise UserError(
                    _(
                        "You can't register a payment because "
                        "there is nothing same PIT document."
                    )
                )
        return super().default_get(fields_list)
