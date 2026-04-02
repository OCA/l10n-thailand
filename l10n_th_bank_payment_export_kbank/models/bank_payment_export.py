# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import ValidationError


class BankPaymentExport(models.Model):
    _inherit = "bank.payment.export"

    bank = fields.Selection(
        selection_add=[("KASITHBK", "KBank")],
        ondelete={"KASITHBK": "cascade"},
    )
    kbank_transfer_type = fields.Selection(
        related="bank_template_id.kbank_transfer_type",
        store=True,
        string="Transfer Type",
    )
    # Common KBank
    kbank_charge_bearer = fields.Selection(
        selection=[
            ("Y", "Y - Beneficiary"),
            ("N", "N - Client"),
        ],
        string="Charges For A/C of",
    )
    # Same Bank
    kbank_product_type = fields.Selection(
        selection=[
            ("FTR", "FTR - Inter Account Funds Transfer"),
            ("FTL", "FTL - Third Party Funds Transfer"),
            ("PCT", "PCT - KBank Payroll"),
            ("DCT", "DCT - Direct Credit"),
        ],
        string="Product Type",
    )
    # Other Bank
    kbank_payment_type = fields.Selection(
        selection=[
            ("MCL", "MCL - SMART Credit Next Day"),
            ("MCS", "MCS - SMART Credit Same Day"),
            ("BNL", "BNL - Bahtnet"),
            ("PCL", "PCL - SMART Credit Next Day"),
            ("IPP", "IPP - Interbank Transfer"),
        ],
        string="Payment Type",
    )

    def _check_constraint_line(self):
        self.ensure_one()
        res = super()._check_constraint_line()

        # Required SMS, SMS Lang for Other Bank or Same Bank (FTL, DCT)
        is_other_bank = self.kbank_transfer_type == "other_bank"
        is_special_same_bank = (
            self.kbank_transfer_type == "same_bank"
            and self.kbank_product_type in ("FTL", "DCT")
        )
        if is_other_bank or is_special_same_bank:
            partners = self.export_line_ids.mapped("payment_id.partner_id")
            missing_sms = partners.filtered(lambda p: not p.kbank_sms)

            if missing_sms:
                names = "\n".join(f"- {p.name}" for p in missing_sms)

                raise ValidationError(
                    self.env._(
                        "The following partners do not have SMS configured:\n%s\n\n"
                        "Please update the KBank SMS field in the partner."
                    )
                    % names
                )

        return res
