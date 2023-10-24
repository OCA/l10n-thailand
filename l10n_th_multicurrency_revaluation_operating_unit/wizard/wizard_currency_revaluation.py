# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class WizardCurrencyRevaluation(models.TransientModel):
    _inherit = "wizard.currency.revaluation"

    def _write_adjust_balance(
        self, account, currency, partner_id, amount, label, form, sums
    ):
        created_ids = super(WizardCurrencyRevaluation, self)._write_adjust_balance(
            account, currency, partner_id, amount, label, form, sums
        )
        ou_id = form.journal_id.operating_unit_id.id
        if ou_id:
            self.env["account.move.line"].browse(created_ids).write(
                {"operating_unit_id": ou_id}
            )
            self.env["account.move"].search([("line_ids", "in", created_ids)]).write(
                {"operating_unit_id": ou_id}
            )
        return created_ids
