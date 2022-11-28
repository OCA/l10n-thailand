# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _add_deduction(
        self, wht_lines, wht_tax, partner_id, amount_deduct, currency, date
    ):
        deduct, amount_deduct = super()._add_deduction(
            wht_lines, wht_tax, partner_id, amount_deduct, currency, date
        )
        deduct["analytic_account_id"] = wht_lines.analytic_account_id.id
        deduct["analytic_tag_ids"] = wht_lines.analytic_tag_ids.ids
        return deduct, amount_deduct
