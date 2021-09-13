# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_th_withholding_tax_cert.models.withholding_tax_cert import (
    WHT_CERT_INCOME_TYPE,
)


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payments = super()._create_payments()
        for payment in payments:
            move_ids = payment.reconciled_bill_ids.filtered("account_pit")
            if move_ids:
                payment.write(
                    {
                        "pit_line": [
                            (
                                0,
                                0,
                                {
                                    "partner_id": payment.partner_id.id,
                                    "wht_cert_income_type": move_ids[
                                        0
                                    ].pit_wht_cert_income_type
                                    or False,
                                    "amount_income": sum(
                                        move_ids.mapped("amount_untaxed")
                                    )
                                    or 0.0,
                                    "amount_wht": self.payment_difference,
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
        move_id = self.env["account.move"].browse(self._context.get("active_ids", []))
        if (
            len(move_id) == 1
            and move_id.account_pit
            and not any(line.wt_tax_id for line in move_id.line_ids)
        ):
            PIT = self.env["personal.income.tax"]
            pit_date = self._context.get("pit_date", False)
            pit_amount_year = self._get_pit_amount_yearly(self.partner_id)
            base_amount = move_id.amount_untaxed or 0.0
            total_pit = pit_amount_year + base_amount
            expected_wht = PIT.calculate_rate_wht(total_pit, base_amount, date=pit_date)
            if expected_wht:
                self.amount -= expected_wht
                self.payment_difference_handling = "reconcile"
                self.writeoff_label = (
                    dict(WHT_CERT_INCOME_TYPE).get(
                        move_id.pit_wht_cert_income_type, False
                    )
                    or self.writeoff_label
                )
        return res

    @api.model
    def default_get(self, fields_list):
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", False)
            move_ids = self.env["account.move"].browse(active_ids)
            account_pits = move_ids.filtered("account_pit")
            if len(move_ids) > 1 and account_pits:
                raise UserError(
                    _("You can't register a payment on tree view with account pit.")
                )
        return super().default_get(fields_list)
