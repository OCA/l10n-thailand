# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPaymentRegisterOrder(models.Model):
    _inherit = "account.payment.register.order"

    def action_create_payments(self):
        """Send context netting and move_ids to module account_payment_netting"""
        self.ensure_one()
        if self.netting:
            self = self.with_context(
                netting=1, active_ids=self.line_ids.mapped("move_id").ids
            )
        return super().action_create_payments()
