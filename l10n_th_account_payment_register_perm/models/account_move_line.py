# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _all_reconciled_lines(self):
        # Resorting, with id, to ensure that prior ID will be reconciled first
        if self._context.get("reduced_line_sorting"):
            self = self.sorted(
                key=lambda line: (
                    line.date_maturity or line.date,
                    line.id,  # add sort by id
                    line.currency_id,
                )
            )
        else:
            self = self.sorted(
                lambda line: (
                    line.date_maturity or line.date,
                    line.id,  # add sort by id
                    line.currency_id,
                    line.amount_currency,
                )
            )
        # --
        return super()._all_reconciled_lines()
