# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import format_date


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _update_payment_register(self, amount_base, amount_wt, wht_move_lines):
        updated = super()._update_payment_register(
            amount_base, amount_wt, wht_move_lines
        )
        if not updated and len(wht_move_lines) > 1:  # good for multi deduct
            self.payment_difference_handling = "reconcile_multi_deduct"
            self._onchange_payment_difference_handling()
        return True

    @api.onchange("payment_difference_handling")
    def _onchange_payment_difference_handling(self):
        if not self.payment_difference_handling == "reconcile_multi_deduct":
            return
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            moves = self.env["account.move"].browse(active_ids)
            move_lines = moves.mapped("line_ids").filtered("wht_tax_id")
            if move_lines:
                # Case WHT only, ensure only 1 wizard
                self.ensure_one()
                deductions = [(5, 0, 0)]
                amount_deduct = 0
                wht_taxes = move_lines.mapped("wht_tax_id")
                for wht_tax in wht_taxes:
                    wht_tax_lines = move_lines.filtered(
                        lambda l: l.wht_tax_id == wht_tax
                    )
                    amount_base, amount_wt = wht_tax_lines._get_wht_amount(
                        self.currency_id, self.payment_date
                    )
                    amount_deduct += amount_wt
                    deduct = {
                        "wht_amount_base": amount_base,
                        "wht_tax_id": wht_tax.id,
                        "account_id": wht_tax.account_id.id,
                        "name": wht_tax.display_name,
                        "amount": amount_wt,
                    }
                    deductions.append((0, 0, deduct))
                self.deduction_ids = deductions
                # Set amount only first time
                if float_compare(self.payment_difference, 0.0, 2) == 0:
                    self.amount -= amount_deduct
                    self._compute_payment_difference()

    def _prepare_deduct_move_line(self, deduct):
        res = super()._prepare_deduct_move_line(deduct)
        res.update(
            {
                "wht_tax_id": deduct.wht_tax_id.id,
                "wht_amount_base": deduct.wht_amount_base,
            }
        )
        return res

    def _create_payments(self):
        payments = super()._create_payments()
        # Create account.withholding.move from table multi deduction
        if (
            self.payment_difference_handling == "reconcile_multi_deduct"
            and self.group_payment
            and self.deduction_ids
        ):
            vals = []
            for deduct in self.deduction_ids:
                vals.append(
                    (
                        0,
                        0,
                        self._prepare_withholding_move(
                            deduct.payment_id.partner_id,
                            deduct.payment_id.payment_date,
                            deduct.wht_tax_id,
                            deduct.wht_amount_base,
                            deduct.amount,
                            deduct.payment_id.currency_id,
                            deduct.payment_id.company_id,
                        ),
                    )
                )
            payments[0].write({"wht_move_ids": vals})
        return payments


class AccountPaymentDeduction(models.TransientModel):
    _inherit = "account.payment.deduction"

    wht_tax_id = fields.Many2one(
        string="Withholding Tax",
        comodel_name="account.withholding.tax",
        help="Optional hidden field to keep wht_tax. Useful for case 1 tax only",
    )
    wht_amount_base = fields.Monetary(
        string="Withholding Base",
        help="Based amount for the tax amount",
    )

    @api.onchange("open")
    def _onchange_open(self):
        super()._onchange_open()
        if self.open:
            self.wht_tax_id = False
            self.wht_amount_base = False

    @api.onchange("wht_tax_id", "wht_amount_base")
    def _onchange_wht_tax_id(self):
        if self.wht_tax_id and self.wht_amount_base:
            if self.wht_tax_id.is_pit:
                self._onchange_pit()
            else:
                self._onchange_wht()

    def _onchange_wht(self):
        """ Onchange set for normal withholding tax """
        amount_wt = self.wht_tax_id.amount / 100 * self.wht_amount_base
        self.amount = amount_wt
        self.account_id = self.wht_tax_id.account_id
        self.name = self.wht_tax_id.display_name

    def _onchange_pit(self):
        """ Onchange set for personal income tax """
        if not self.wht_tax_id.pit_id:
            raise UserError(
                _("No effective PIT rate for date %s")
                % format_date(self.env, self.payment_id.payment_date)
            )
        payment = self.payment_id
        company = payment.company_id
        amount_base_company = payment.currency_id._convert(
            self.wht_amount_base,
            company.currency_id,
            company,
            payment.payment_date,
        )
        amount_pit_company = self.wht_tax_id.pit_id._compute_expected_wt(
            payment.partner_id,
            amount_base_company,
            pit_date=payment.payment_date,
            currency=company.currency_id,
            company=company,
        )
        amount_pit = company.currency_id._convert(
            amount_pit_company,
            payment.currency_id,
            company,
            payment.payment_date,
        )
        self.amount = amount_pit
        self.account_id = self.wht_tax_id.account_id
        self.name = self.wht_tax_id.display_name
