# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class BankPaymentExportLine(models.Model):
    _name = "bank.payment.export.line"
    _inherit = ["bank.payment.export.line", "base.cancel.confirm"]

    _has_cancel_reason = "optional"  # ["no", "optional", "required"]

    def action_reject(self):
        if not self.filtered("cancel_confirm"):
            return self.open_cancel_confirm_wizard()
        return super().action_reject()

    def _action_reject_bank_payment(self):
        reason_cancel_all = ", ".join(
            self.payment_export_id.export_line_ids.mapped("cancel_reason")
        )
        self.payment_export_id.write(
            {"cancel_confirm": True, "cancel_reason": reason_cancel_all}
        )
        return super()._action_reject_bank_payment()
