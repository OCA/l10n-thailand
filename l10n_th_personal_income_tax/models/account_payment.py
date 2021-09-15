# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    pit_line = fields.One2many(
        comodel_name="pit.move",
        inverse_name="payment_id",
        string="Tax Line PIT",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    def action_cancel(self):
        res = super().action_cancel()
        for payment in self:
            # Create the mirror only for those posted
            for line in payment.pit_line:
                line.copy(
                    {
                        "amount_income": -line.amount_income,
                        "amount_wt": -line.amount_wt,
                    }
                )
                line.cancelled = True
        return res
