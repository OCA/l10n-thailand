# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _update_payment_register(self, amount_wt, inv_lines):
        super()._update_payment_register(amount_wt, inv_lines)
        if len(inv_lines) > 1:
            self.payment_difference_handling = "reconcile_multi_deduct"
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
                deductions = [(5, 0, 0)]
                for line in inv_lines:
                    deduct = {
                        "wt_tax_id": line.wt_tax_id.id,
                        "account_id": line.wt_tax_id.account_id.id,
                        "name": line.wt_tax_id.display_name,
                        "amount": -line.wt_tax_id.amount / 100 * line.price_subtotal,
                    }
                    deductions.append((0, 0, deduct))
                self.deduction_ids = deductions

    def _prepare_deduct_move_line(self, deduct):
        res = super()._prepare_deduct_move_line(deduct)
        res.update({"wt_tax_id": deduct.wt_tax_id.id})
        return res


class AccountPaymentDeduction(models.Model):
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
