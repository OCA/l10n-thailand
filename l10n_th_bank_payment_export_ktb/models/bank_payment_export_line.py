# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import float_round


class BankPaymentExportLine(models.Model):
    _inherit = "bank.payment.export.line"

    def _get_receiver_information(self):
        (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        ) = super()._get_receiver_information()
        if self.payment_export_id.bank == "KRTHTHBK":
            receiver_name = (
                receiver_name and receiver_name[:100].ljust(100) or "".ljust(100)
            )
            receiver_bank_code = (
                receiver_bank_code and receiver_bank_code[:3].zfill(3) or "---"
            )
            receiver_branch_code = (
                receiver_branch_code and receiver_branch_code[:4].zfill(4) or "----"
            )
        return (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        )

    def _get_sender_information(self):
        (
            sender_bank_code,
            sender_branch_code,
            sender_acc_number,
        ) = super()._get_sender_information()
        if self.payment_export_id.bank == "KRTHTHBK":
            sender_bank_code = (
                sender_bank_code and sender_bank_code[:3].zfill(3) or "---"
            )
            sender_branch_code = (
                sender_branch_code and sender_branch_code[:4].zfill(4) or "----"
            )
            sender_acc_number = (
                sender_acc_number and sender_acc_number[:11].zfill(11) or "-----------"
            )
        return sender_bank_code, sender_branch_code, sender_acc_number

    def _get_amount_no_decimal(self, amount, digits=False):
        if self.payment_export_id.bank == "KRTHTHBK":
            return int(round(float_round(amount * 100, precision_rounding=1), digits))
        return super()._get_amount_no_decimal(amount, digits)
