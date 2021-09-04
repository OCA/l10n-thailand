# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models
from odoo.tools import float_compare


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.depends("amount")
    def _compute_payment_difference(self):
        super()._compute_payment_difference()
        for rec in self:
            if float_compare(rec.payment_difference, 0.0, 2) == 0:
                rec.payment_difference_handling = "open"

    def _update_payment_register(self, amount_wt, inv_lines):
        super()._update_payment_register(amount_wt, inv_lines)
        move_ids = inv_lines.mapped("move_id")
        amount_residual = sum(move_ids.mapped("amount_residual"))
        amount_total = sum(move_ids.mapped("amount_total"))
        if float_compare(amount_residual, amount_total, 2) == 0 and len(inv_lines) > 1:
            self.payment_difference_handling = "reconcile_multi_deduct"
            self._onchange_payment_difference_handling()
        return True

    @api.onchange("payment_difference_handling")
    def _onchange_payment_difference_handling(self):
        if not self.payment_difference_handling == "reconcile_multi_deduct":
            return
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            inv_lines = invoices.mapped("invoice_line_ids").filtered("wt_tax_id")
            if inv_lines:
                # Case WHT only, ensure only 1 wizard
                self.ensure_one()
                deductions = [(5, 0, 0)]
                for line in inv_lines:
                    base_amount = line._get_wt_base_amount(
                        self.currency_id, self.payment_date
                    )
                    deduct = {
                        "wt_tax_id": line.wt_tax_id.id,
                        "account_id": line.wt_tax_id.account_id.id,
                        "name": line.wt_tax_id.display_name,
                        "amount": line.wt_tax_id.amount / 100 * base_amount,
                    }
                    deductions.append((0, 0, deduct))
                self.deduction_ids = deductions

    def _prepare_deduct_move_line(self, deduct):
        res = super()._prepare_deduct_move_line(deduct)
        res.update({"wt_tax_id": deduct.wt_tax_id.id})
        return res


class AccountPaymentDeduction(models.TransientModel):
    _inherit = "account.payment.deduction"

    wt_tax_id = fields.Many2one(
        string="Withholding Tax",
        comodel_name="account.withholding.tax",
        help="Optional hidden field to keep wt_tax. Useful for case 1 tax only",
    )

    @api.onchange("wt_tax_id")
    def _onchange_wt_tax_id(self):
        if self.wt_tax_id:
            self.account_id = self.wt_tax_id.account_id
            self.name = self.wt_tax_id.display_name

    @api.onchange("open")
    def _onchange_open(self):
        super()._onchange_open()
        if self.open:
            self.wt_tax_id = False
