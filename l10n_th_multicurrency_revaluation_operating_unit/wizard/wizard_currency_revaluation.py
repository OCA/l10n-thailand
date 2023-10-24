# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class WizardCurrencyRevaluation(models.TransientModel):
    _inherit = "wizard.currency.revaluation"

    def _prepare_base_move(self, amount, sums, form, currency_id):
        """Add operating unit from the move origin.
        If not found, it will be checked from the journal."""
        base_move = super()._prepare_base_move(amount, sums, form, currency_id)
        ml = self.env["account.move.line"].browse(sums.get("id"))
        base_move["operating_unit_id"] = (
            ml.move_id.operating_unit_id.id or self.journal_id.operating_unit_id.id
        )
        return base_move
