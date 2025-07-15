# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentExport(models.Model):
    _inherit = "bank.payment.export"

    bank = fields.Selection(
        selection_add=[("KRTHTHBK", "KTB")],
        ondelete={"KRTHTHBK": "cascade"},
    )
    # Configuration
    ktb_company_id = fields.Char(
        string="KTB Company ID",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ktb_sender_name = fields.Char(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    # filter
    ktb_is_editable = fields.Boolean(
        compute="_compute_ktb_editable",
        string="KTB Editable",
    )
    ktb_bank_type = fields.Selection(
        selection=[
            ("standard", "Standard / Express"),
            ("direct", "Direct"),
        ],
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ktb_service_type_standard = fields.Selection(
        selection=[
            ("01", "01 - เงินเดือน ค่าจ้าง บำเหน็จ บำนาญ"),
            ("02", "02 - เงินปันผล"),
            ("03", "03 - ดอกเบี้ย"),
            ("04", "04 - ค่าสินค้า บริการ"),
            ("05", "05 - ขายหลักทรัพย์"),
            ("06", "06 - คืนภาษี"),
            ("07", "07 - เงินกู้"),
            ("59", "59 - อื่น ๆ"),
        ],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ktb_service_type_direct = fields.Selection(
        selection=[
            ("02", "02 - รายการเข้าบัญชีเงินเดือน (Salary)"),
            ("04", "04 - รายการชำระดอกเบี้ย (Bond Interest)"),
            ("09", "09 - รายการชำระเบี้ยประกัน (Insurance Premium)"),
            ("10", "10 - รายการชำระค่าโทรศัพท์ (Telephone Payment)"),
            ("11", "11 - รายการชำระค่าไฟฟ้า (Electricity Payment)"),
            ("12", "12 - รายการชำระค่าน้ำประปา (Water Payment)"),
            ("14", "14 - รายการชำระค่าสินค้าและบริการ (Purchase & Service)"),
            ("15", "15 - รายการชำระเงินของธนาคารอาคารสงเคราะห์ (GSB)"),
            ("21", "21 - รายการชำระราคาหลักทรัพย์ (Securities)"),
            ("25", "25 - รายการชำระ Clearing Bank"),
            ("27", "27 - รายการชำระค่าประกันสังคม (SSO)"),
            ("28", "28 - รายการชำระของกองสลากฯ (Lottery)"),
            ("37", "37 - รายการชำระด้วยบัตรอิเลคทรอนิคส์ (Electronic Card)"),
            ("46", "46 - รายการจ่ายเงินบำนาญ (Pension Fund)"),
        ],
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.onchange("ktb_bank_type")
    def _onchange_ktb_bank_type(self):
        if self.ktb_bank_type == "standard":
            self.ktb_service_type_direct = False
        else:
            self.ktb_service_type_standard = False

    @api.depends("bank")
    def _compute_required_effective_date(self):
        res = super()._compute_required_effective_date()
        for rec in self.filtered(lambda l: l.bank == "KRTHTHBK"):
            rec.is_required_effective_date = True
        return res

    @api.depends("bank")
    def _compute_ktb_editable(self):
        for export in self:
            export.ktb_is_editable = True if export.bank == "KRTHTHBK" else False

    def _check_constraint_confirm(self):
        res = super()._check_constraint_confirm()
        for rec in self.filtered(lambda l: l.bank == "KRTHTHBK"):
            if not rec.ktb_bank_type:
                raise UserError(_("You need to add 'Bank Type' before confirm."))
            if rec.ktb_bank_type == "direct" and any(
                line.payment_bank_id.bic != rec.bank for line in rec.export_line_ids
            ):
                raise UserError(
                    _("Bank type '{}' can not export payment to other bank.").format(
                        dict(self._fields["ktb_bank_type"].selection).get(
                            self.ktb_bank_type
                        )
                    )
                )
            if rec.ktb_bank_type == "standard" and any(
                line.payment_bank_id.bic == rec.bank for line in rec.export_line_ids
            ):
                raise UserError(
                    _("Bank type '{}' can not export payment to the same bank.").format(
                        dict(self._fields["ktb_bank_type"].selection).get(
                            self.ktb_bank_type
                        )
                    )
                )
        return res

    def _get_context_create_bank_payment_export(self, payments):
        ctx = super()._get_context_create_bank_payment_export(payments)
        partner_bic_bank = list(set(payments.mapped("partner_bank_id.bank_id.bic")))
        # KTB Bank
        if partner_bic_bank and ctx["default_bank"] == "KRTHTHBK":
            # Same bank
            if len(partner_bic_bank) == 1 and partner_bic_bank[0] == "KRTHTHBK":
                ctx.update({"default_ktb_bank_type": "direct"})
            # Other bank
            elif "KRTHTHBK" not in partner_bic_bank:
                ctx.update({"default_ktb_bank_type": "standard"})
        return ctx

    def _check_constraint_line(self):
        # Add condition with line on this function
        res = super()._check_constraint_line()
        self.ensure_one()
        if self.bank == "KRTHTHBK":
            for line in self.export_line_ids:
                if not line.payment_partner_bank_id:
                    raise UserError(
                        _("Recipient Bank with {} is not selected.").format(
                            line.payment_id.name
                        )
                    )
        return res

    def _check_constraint_create_bank_payment_export(self, payments):
        res = super()._check_constraint_create_bank_payment_export(payments)
        payment_bic_bank = list(set(payments.mapped("journal_id.bank_id.bic")))
        payment_bank = len(payment_bic_bank) == 1 and payment_bic_bank[0] or ""
        method_manual_out = self.env.ref("account.account_payment_method_manual_out")
        # Check case KTB must have 1 journal / 1 PE
        if payment_bank == "KRTHTHBK" and len(payments.mapped("journal_id")) > 1:
            raise UserError(
                _("KTB can create bank payment export 1 Journal / 1 Payment Export.")
            )
        for payment in payments:
            if (
                payment.payment_method_id.id != method_manual_out.id
                or payment.journal_id.type != "bank"
            ):
                raise UserError(
                    _(
                        "You can export bank payments with journal 'Bank' "
                        "and Payment method 'Manual' only"
                    )
                )
            if payment.company_id.currency_id != payment.currency_id:
                raise UserError(
                    _("Payments must be currency '{}' only").format(
                        payment.company_id.currency_id.name
                    )
                )
        return res
