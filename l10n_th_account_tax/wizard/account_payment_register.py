# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def _get_default_withhold(self, moves):
        """Withhold PIT by default: PIT is 0% on bills, so there is no residual"""
        withhold = super()._get_default_withhold(moves)
        if withhold == "payment" and any(move._get_pit_taxes() for move in moves):
            withhold = "withhold_pay"
        return withhold

    def _compute_withholding_line_ids(self):
        """Standard only proposes withholding lines for bills with a withholding
        residual. Also propose PIT lines (0% on bills) for the other bills, so that
        the PIT income is always recorded, even when no PIT is withheld."""
        to_init = self.filtered(lambda wizard: not wizard.withholding_line_ids)
        res = super()._compute_withholding_line_ids()
        WithholdingLine = self.env["account.payment.register.withholding.line"]
        for wizard in to_init:
            if not wizard.display_withholding or not wizard.can_edit_wizard:
                continue
            moves = wizard._get_batches()[0]["lines"].move_id.filtered(
                lambda m: (
                    not m.withholding_residual_amount_currency and m._get_pit_taxes()
                )
            )
            base_lines = []
            for move in moves:
                move_base_lines, _move_tax_lines = (
                    move._get_rounded_base_and_tax_lines()
                )
                for base_line in move_base_lines:
                    pit_taxes = (
                        base_line["tax_ids"]
                        .flatten_taxes_hierarchy()
                        .filtered("is_pit")
                    )
                    if pit_taxes:
                        base_lines.append({**base_line, "tax_ids": pit_taxes})
            if base_lines:
                wizard.withholding_line_ids = (
                    WithholdingLine._prepare_withholding_lines_commands(
                        base_lines=base_lines,
                        company=wizard.company_id or self.env.company,
                    )
                )
        return res
