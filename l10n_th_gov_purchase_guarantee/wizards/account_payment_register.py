# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payments = super()._create_payments()
        # Guarantee return date = vendor payment date
        purchase_return_guarantee_ids = self.line_ids.move_id.return_guarantee_ids
        if purchase_return_guarantee_ids:
            purchase_return_guarantee_ids.write({"date_return": self.payment_date})
        return payments
