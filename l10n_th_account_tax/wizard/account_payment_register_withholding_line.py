# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class AccountPaymentRegisterWithholdingLine(models.TransientModel):
    _inherit = "account.payment.register.withholding.line"

    def _get_pit_sibling_lines(self):
        return self.payment_register_id.withholding_line_ids

    @api.depends(
        "payment_register_id.partner_id",
        "payment_register_id.withholding_line_ids.base_amount",
    )
    def _compute_amount(self):
        return super()._compute_amount()
