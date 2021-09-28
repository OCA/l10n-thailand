# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.onchange("wt_tax_id", "wt_amount_base")
    def _onchange_wt_tax_id(self):
        if self.wt_tax_id and self.wt_amount_base:
            if self.wt_tax_id.account_pit:
                # Calculate PIT amount by PIT Rates
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
                    currency=self.currency_id,
                    company=self.company_id,
                )
                amount_pit = self.company_id.currency_id._convert(
                    amount_pit_company,
                    self.currency_id,
                    self.company_id,
                    self.payment_date,
                )
                self.amount = self.source_amount_currency - amount_pit
                self.writeoff_account_id = self.wt_tax_id.account_id
                self.writeoff_label = self.wt_tax_id.display_name
            else:
                super()._onchange_wt_tax_id()

    def _create_payments(self):
        payments = super()._create_payments()
        if (
            self.group_payment
            and self.wt_tax_id.account_pit
            and self.payment_difference
        ):
            amount_income = self.currency_id._convert(
                self.wt_amount_base,
                self.company_id.currency_id,
                self.company_id,
                self.payment_date,
            )
            amount_wt = self.currency_id._convert(
                self.payment_difference,
                self.company_id.currency_id,
                self.company_id,
                self.payment_date,
            )
            vals = {
                "partner_id": self.partner_id.id,
                "amount_income": amount_income,
                "amount_wt": amount_wt,
            }
            payments[0].write({"pit_line": [(0, 0, vals)]})
        return payments
