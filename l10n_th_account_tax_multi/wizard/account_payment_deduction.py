# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class AccountPaymentDeduction(models.TransientModel):
    _inherit = "account.payment.deduction"

    @api.depends("payment_id")
    def _compute_analytic_multi_deduction(self):
        return
