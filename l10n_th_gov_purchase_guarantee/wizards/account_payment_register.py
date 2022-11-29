# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payments = super()._create_payments()
        # Guarantee return date = vendor payment date
        active_model = self._context.get("active_model")
        active_ids = self._context.get("active_ids")  # must use active_ids
        if active_model == "account.move" and active_ids:
            moves = self.env[active_model].browse(active_ids).sudo()
            move_return_guarantee_ids = moves.filtered(lambda l: l.return_guarantee_ids)
            for move in move_return_guarantee_ids:
                move.return_guarantee_ids.date_return = self.payment_date
        return payments
