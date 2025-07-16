# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.base.models.res_bank import sanitize_account_number


class BankPaymentExportCommon(models.AbstractModel):
    _name = "bank.payment.export.common"
    _description = "Bank Payment Export Common"

    def _get_payment_net_amount(self):
        payment_net_amount = self.payment_amount
        return payment_net_amount

    def _get_amount_no_decimal(self, amount, digits=False):
        """Implementation is available"""
        return amount

    def _get_acc_number_digit(self, partner_bank_id):
        acc_number = partner_bank_id.acc_number
        if not acc_number:
            return "**receiver account number is null**"
        sanitize_acc_number = sanitize_account_number(acc_number)
        if len(sanitize_acc_number) <= 11:
            return sanitize_acc_number.zfill(11)
        # BAAC: ธ. เพื่อการเกษตรและสหกรณ์การเกษตร
        # HSBC: ธ. ฮ่องกงและเซี่ยงไฮ้แบงกิ้งคอร์ปอเรชั่น จำกัด
        if partner_bank_id.bank_id.bic in ("BAABTHBK", "HSBCTHBK"):
            return (
                len(sanitize_acc_number) == 12
                and sanitize_acc_number[1:]
                or "**Digit account number is not correct**"
            )
        # TISCO: ธ. ทิสโก้ จำกัด (มหาชน)
        # KKP: ธ. เกียรตินาคิน จำกัด (มหาชน)
        if partner_bank_id.bank_id.bic in ("TFPCTHB1", "KKPBTHBK"):
            return (
                len(sanitize_acc_number) == 14
                and sanitize_acc_number[4:].zfill(11)
                or "**Digit account number is not correct**"
            )
        # IBANK: ธ. อิสลามแห่งประเทศไทย (For 12 digits)
        if partner_bank_id.bank_id.bic == "TIBTTHBK":
            return (
                len(sanitize_acc_number) == 12
                and sanitize_acc_number[2:].zfill(11)
                or "**Digit account number is not correct**"
            )
        # GSB: ธ. ออมสิน
        if partner_bank_id.bank_id.bic == "GSBATHBK":
            if len(sanitize_acc_number) == 12:
                sanitize_acc_number = "".join(["999", sanitize_acc_number])
            return (
                len(sanitize_acc_number) == 15
                and sanitize_acc_number[4:]
                or "**Digit account number is not correct**"
            )
        return sanitize_acc_number

    def _get_receiver_information(self):
        self.ensure_one()
        partner_bank_id = self.payment_partner_bank_id
        receiver_name = (
            partner_bank_id.acc_holder_name or partner_bank_id.partner_id.display_name
        )
        receiver_bank_code = partner_bank_id.bank_id.bank_code
        receiver_branch_code = partner_bank_id.bank_id.bank_branch_code
        receiver_acc_number = self._get_acc_number_digit(partner_bank_id)
        return (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        )

    def _get_sender_information(self):
        self.ensure_one()
        # Sender
        sender_journal_id = self.payment_id.journal_id
        sender_bank_code = sender_journal_id.bank_id.bank_code
        sender_branch_code = sender_journal_id.bank_id.bank_branch_code
        sender_acc_number = sanitize_account_number(
            sender_journal_id.bank_account_id.acc_number
        )
        return sender_bank_code, sender_branch_code, sender_acc_number
