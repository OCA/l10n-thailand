# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_wht_base_amount(self, currency, currency_date):
        self.ensure_one()
        wht_base_amount = super()._get_wht_base_amount(currency, currency_date)
        if self.env.context.get("netting"):
            active_ids = self.env.context.get("active_ids")
            moves = self.env["account.move"].browse(active_ids)
            type_netting = sum(moves.mapped("amount_residual_signed"))
            # Netting more than 0 = 'inbound'
            # Netting less than 0 = 'outbound'
            if (type_netting > 0.0 and wht_base_amount > 0.0) or (
                type_netting < 0.0 and wht_base_amount < 0.0
            ):
                wht_base_amount *= -1
        return wht_base_amount
