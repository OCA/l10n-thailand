# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    proxy_type = fields.Selection(
        selection_add=[
            ("ewallet_id", "Ewallet ID"),
            ("merchant_tax_id", "Merchant Tax ID"),
            ("mobile", "Mobile Number"),
            ("bill_payment", "Bill Payment"),
        ],
        ondelete={
            "ewallet_id": "set default",
            "merchant_tax_id": "set default",
            "mobile": "set default",
            "bill_payment": "set default",
        },
    )

    @api.constrains("proxy_type", "proxy_value", "partner_id")
    def _check_th_proxy(self):
        tax_id_re = re.compile(r"^[0-9]{13}$")
        mobile_re = re.compile(r"^[0-9]{10}$")
        biller_id_re = re.compile(r"^[0-9]{15}$")
        for bank in self.filtered(lambda b: b.country_code == "TH"):
            if bank.proxy_type == "merchant_tax_id" and (
                not bank.proxy_value or not tax_id_re.match(bank.proxy_value)
            ):
                raise ValidationError(
                    self.env._(
                        "The Merchant Tax ID must be in the format "
                        f"1234567890123 for account number {bank.acc_number}.",
                    )
                )
            if bank.proxy_type == "mobile" and (
                not bank.proxy_value or not mobile_re.match(bank.proxy_value)
            ):
                raise ValidationError(
                    self.env._(
                        "The Mobile Number must be in the format "
                        f"0812345678 for account number {bank.acc_number}.",
                    )
                )
            if bank.proxy_type == "bill_payment" and (
                not bank.proxy_value or not biller_id_re.match(bank.proxy_value)
            ):
                raise ValidationError(
                    self.env._(
                        "The Bill payment must be in the format 15 digits "
                        f"for account number {bank.acc_number}.",
                    )
                )

    @api.depends("country_code")
    def _compute_display_qr_setting(self):
        bank_th = self.filtered(lambda b: b.country_code == "TH")
        bank_th.display_qr_setting = True
        return super(ResPartnerBank, self - bank_th)._compute_display_qr_setting()

    def _get_merchant_account_info(self):
        if self.country_code == "TH":
            if self.proxy_type == "bill_payment":
                tag_id = 30  # PromptPay - Bill Payment
                proxy_value = self.proxy_value.zfill(15)
                ref1 = self.env.context.get("bill_ref1", "")
                ref2 = self.env.context.get("bill_ref2", "")
                vals = [
                    (0, "A000000677010112"),  # AID
                    (1, proxy_value),  # Biller ID (15 digits) <- sub-tag 01
                    (2, ref1),  # Ref1 <- sub-tag 02
                    (3, ref2),  # Ref2 <- sub-tag 03
                ]
            else:
                tag_id = 29  # PromptPay - Credit Transfer with PromptPayID
                proxy_type_mapping = {
                    "mobile": 1,
                    "merchant_tax_id": 2,
                    "ewallet_id": 3,
                }
                proxy_value = (
                    re.sub(r"^0", "66", self.proxy_value).zfill(13)
                    if self.proxy_type == "mobile"
                    else self.proxy_value
                )
                vals = [
                    (0, "A000000677010111"),
                    (proxy_type_mapping[self.proxy_type], proxy_value),
                ]
            return (tag_id, "".join([self._serialize(*val) for val in vals]))
        return super()._get_merchant_account_info()

    def _get_error_messages_for_qr(self, qr_method, debtor_partner, currency):
        if qr_method == "emv_qr" and self.country_code == "TH":
            if currency.name not in ["THB"]:
                return self.env._(
                    "Can't generate a PromptPay QR code with a currency other than THB."
                )
            return None
        return super()._get_error_messages_for_qr(qr_method, debtor_partner, currency)

    def _check_for_qr_code_errors(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        if (
            qr_method == "emv_qr"
            and self.country_code == "TH"
            and self.proxy_type
            not in ["ewallet_id", "merchant_tax_id", "mobile", "bill_payment"]
        ):
            return self.env._(
                "The PromptPay Type must be either Ewallet ID, "
                "Merchant Tax ID, Mobile Number or Bill Payment to generate "
                "a Thailand Bank QR code"
            )
        return super()._check_for_qr_code_errors(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )
