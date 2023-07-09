# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import Decimal

from odoo import api, fields, models

from odoo.addons.base.models.res_bank import sanitize_account_number


class BankPaymentExportLine(models.Model):
    _inherit = "bank.payment.export.line"

    scb_beneficiary_noti = fields.Selection(
        selection=[
            ("N", "N - None"),
            ("F", "F - Fax"),
            ("S", "S - SMS"),
            ("E", "E - Email"),
        ],
        compute="_compute_default_scb_config",
        store=True,
        readonly=False,
    )
    scb_beneficiary_phone = fields.Char(size=10)
    scb_beneficiary_email = fields.Char(size=100)  # Support outward remittance
    scb_beneficiary_charge = fields.Boolean(
        compute="_compute_beneficiary_charge_line",
        store=True,
        readonly=False,
    )
    # Outward Remittance
    scb_customer_ref1 = fields.Char(
        string="Customer Ref1",
        size=32,
    )
    scb_customer_ref2 = fields.Char(
        string="Customer Ref2",
        size=32,
    )

    @api.depends("payment_partner_id")
    def _compute_default_scb_config(self):
        for rec in self:
            rec.scb_beneficiary_noti = rec.payment_partner_id.scb_beneficiary_noti
            rec.onchange_beneficiary_noti()
            # Outward Remittance
            rec.scb_customer_ref1 = rec.payment_partner_id.scb_customer_ref1
            rec.scb_customer_ref2 = rec.payment_partner_id.scb_customer_ref2

    @api.depends("payment_export_id.scb_beneficiary_charge")
    def _compute_beneficiary_charge_line(self):
        for rec in self:
            rec.scb_beneficiary_charge = rec.payment_export_id.scb_beneficiary_charge

    @api.onchange("scb_beneficiary_noti")
    def onchange_beneficiary_noti(self):
        if self.scb_beneficiary_noti == "E":
            self.scb_beneficiary_phone = self.scb_beneficiary_phone or False
            self.scb_beneficiary_email = self.payment_partner_id.scb_email_partner
        elif self.scb_beneficiary_noti == "F":
            self.scb_beneficiary_phone = self.payment_partner_id.scb_phone_partner
            self.scb_beneficiary_email = self.scb_beneficiary_email or False
        elif self.scb_beneficiary_noti == "S":
            self.scb_beneficiary_phone = self.payment_partner_id.scb_sms_partner
            self.scb_beneficiary_email = self.scb_beneficiary_email or False

    def _get_receiver_information(self):
        (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        ) = super()._get_receiver_information()
        if self.payment_export_id.bank == "SICOTHBK":
            # DCP get only 10 digits
            if self.payment_export_id.scb_product_code == "DCP":
                receiver_acc_number = receiver_acc_number[1:]
            # BNT return following original
            if self.payment_export_id.scb_product_code == "BNT":
                receiver_acc_number = sanitize_account_number(
                    self.payment_partner_bank_id.acc_number or "-----"
                )
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
        if self.payment_export_id.bank == "SICOTHBK":
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

    def _get_scb_amount_no_decimal(self, amount, digits=16, is_round=True):
        if is_round:
            amount = round(amount, 2)
        return str(int(Decimal(str(amount)) * 1000)).zfill(digits)

    def _get_payee_fax(self):
        return self.scb_beneficiary_phone if self.scb_beneficiary_noti == "F" else ""

    def _get_payee_sms(self):
        return self.scb_beneficiary_phone if self.scb_beneficiary_noti == "S" else ""

    def _get_payee_email(self):
        return self.scb_beneficiary_email if self.scb_beneficiary_noti == "E" else ""
