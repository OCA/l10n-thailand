# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.base.models.res_bank import sanitize_account_number


class BankPaymentExportCommon(models.AbstractModel):
    _name = "bank.payment.export.common"
    _description = "Common Function for Bank Payment Export File"

    def _get_receiver_address(self, object_address):
        receiver_address = " ".join(
            [
                object_address.street or "",
                object_address.street2 or "",
                object_address.city or "",
                object_address.zip or "",
            ]
        )
        return receiver_address

    def _get_address(self, object_address, max_length):
        receiver_address = self._get_receiver_address(object_address)
        address = receiver_address[:max_length]
        return address

    def _format_amount(self, amount, decimals=2):
        """Format amount as zero-padded string with configurable decimal places.
        :param amount: numeric amount to format
        :param decimals: number of decimal digits (default 2)
        :return: zero-padded amount string
        """
        amount_str = f"{amount:.{decimals}f}"
        return amount_str

    def _get_amount_wht_invoice(self, inv, line):
        """get amount wht from invoice"""
        amount_wht = 0.0
        if hasattr(inv.invoice_line_ids, "wht_tax_id"):
            wht_lines = inv.invoice_line_ids.filtered("wht_tax_id")
            amount_wht = wht_lines._get_wht_amount(
                self.env.company.currency_id, line.payment_date
            )[1]
        return amount_wht


class BankPaymentExportLineCommon(models.AbstractModel):
    _name = "bank.payment.export.line.common"
    _description = "Common Function for Bank Payment Export Line File"

    def sanitize_account_number(self, acc_number):
        if not acc_number:
            return ""
        return sanitize_account_number(acc_number)

    def _format_amount(self, amount, decimals=2):
        """Format amount as zero-padded string with configurable decimal places.
        :param amount: numeric amount to format
        :param decimals: number of decimal digits (default 2)
        :return: zero-padded amount string
        """
        amount_str = f"{amount:.{decimals}f}"
        return amount_str

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
