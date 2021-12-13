# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _prepare_writeoff_move_line(self):
        writeoff_move_line = super()._prepare_writeoff_move_line()
        expense_sheet_ids = self._context.get("expense_sheet_ids", False)
        if expense_sheet_ids:
            sheets = self.env["hr.expense.sheet"].browse(expense_sheet_ids)
            partner = sheets.expense_line_ids.mapped("bill_partner_id")
            if len(partner) > 1:
                raise UserError(
                    _(
                        "You can not register payment withholding tax with multi vendors."
                    )
                )
            writeoff_move_line["partner_id"] = partner.id
        return writeoff_move_line
