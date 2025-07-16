# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.base.models.res_bank import sanitize_account_number


class BankPaymentExportCommon(models.AbstractModel):
    _name = "bank.payment.export.common"
    _description = "Bank Payment Export File"

    def sanitize_account_number(self, acc_number):
        if not acc_number:
            return ""
        return sanitize_account_number(acc_number)

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
        # GHB: ธ. อาคารสงเคราะห์
        if partner_bank_id.bank_id.bic in ("GSBATHBK", "GOHUTHB1"):
            if len(sanitize_acc_number) == 12:
                sanitize_acc_number = "".join(["999", sanitize_acc_number])
            return (
                len(sanitize_acc_number) == 15
                and sanitize_acc_number[4:]
                or "**Digit account number is not correct**"
            )
        return sanitize_acc_number

    def _get_receiver_branch_code_gsb(self):
        """For GSBATHBK (ธ.ออมสิน)"""
        receiver_branch_code = ""
        sanitize_acc_number = sanitize_account_number(
            self.payment_partner_bank_id.acc_number
        )
        if len(sanitize_acc_number) == 12:
            receiver_branch_code = "".join(["999", sanitize_acc_number[:1]])
        if len(sanitize_acc_number) == 15:
            receiver_branch_code = sanitize_acc_number[:4]
        return receiver_branch_code
