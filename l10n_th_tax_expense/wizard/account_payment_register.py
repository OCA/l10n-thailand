# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        """ Find vendor expense for update partner journal items withholding tax """
        self.ensure_one()
        payments = super()._create_payments()
        expense_sheet_ids = self.env.context.get("expense_sheet_ids")
        if (
            self.payment_difference_handling == "reconcile"
            and self.writeoff_account_id.wht_account
            and self.wht_amount_base
            and expense_sheet_ids
        ):
            sheets = self.env["hr.expense.sheet"].browse(expense_sheet_ids)
            partner = sheets.expense_line_ids.mapped("bill_partner_id")
            if len(partner) > 1:
                raise UserError(
                    _(
                        "You can not register payment withholding tax with multi vendors."
                    )
                )
            ml_wht_tax = payments.with_context(
                skip_account_move_synchronization=1
            ).move_id.line_ids.filtered(lambda l: l.wht_tax_id)
            ml_wht_tax.write({"partner_id": partner.id})
        return payments
