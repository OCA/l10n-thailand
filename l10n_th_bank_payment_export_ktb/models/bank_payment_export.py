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
            ("01", "เงินเดือน ค่าจ้าง บำเหน็จ บำนาญ"),
            ("02", "เงินปันผล"),
            ("03", "ดอกเบี้ย"),
            ("04", "ค่าสินค้า บริการ"),
            ("05", "ขายหลักทรัพย์"),
            ("06", "คืนภาษี"),
            ("07", "เงินกู้"),
            ("59", "อื่น ๆ"),
        ],
        ondelete={
            "01": "cascade",
            "02": "cascade",
            "03": "cascade",
            "04": "cascade",
            "05": "cascade",
            "06": "cascade",
            "07": "cascade",
            "59": "cascade",
        },
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ktb_service_type_direct = fields.Selection(
        selection=[
            ("02", "รายการเข้าบัญชีเงินเดือน (Salary)"),
            ("04", "รายการชำระดอกเบี้ย (Bond Interest)"),
            ("09", "รายการชำระเบี้ยประกัน (Insurance Premium)"),
            ("10", "รายการชำระค่าโทรศัพท์ (Telephone Payment)"),
            ("11", "รายการชำระค่าไฟฟ้า (Electricity Payment)"),
            ("12", "รายการชำระค่าน้ำประปา (Water Payment)"),
            ("14", "รายการชำระค่าสินค้าและบริการ (Purchase & Service)"),
            ("15", "รายการชำระเงินของธนาคารอาคารสงเคราะห์ (GSB)"),
            ("21", "รายการชำระราคาหลักทรัพย์ (Securities)"),
            ("25", "รายการชำระ Clearing Bank"),
            ("27", "รายการชำระค่าประกันสังคม (SSO)"),
            ("28", "รายการชำระของกองสลากฯ (Lottery)"),
            ("37", "รายการชำระด้วยบัตรอิเลคทรอนิคส์ (Electronic Card)"),
            ("46", "รายการจ่ายเงินบำนาญ (Pension Fund)"),
        ],
        ondelete={
            "02": "cascade",
            "04": "cascade",
            "09": "cascade",
            "10": "cascade",
            "11": "cascade",
            "12": "cascade",
            "14": "cascade",
            "15": "cascade",
            "21": "cascade",
            "25": "cascade",
            "27": "cascade",
            "28": "cascade",
            "37": "cascade",
            "46": "cascade",
        },
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

    def _get_ktb_sender_name(self):
        return self.ktb_sender_name

    def _get_ktb_receiver_info(self, pe_line):
        return "".ljust(8)

    def _get_ktb_receiver_id(self, pe_line):
        return "0".zfill(10)

    def _get_ktb_other_info1(self, pe_line):
        return "".ljust(40)

    def _get_ktb_other_info2(self, pe_line):
        return "".ljust(20)

    def _get_ktb_ddr_ref1(self, pe_line):
        return "".ljust(18)

    def _get_ktb_ddr_ref2(self, pe_line):
        return pe_line.payment_id.name.ljust(18)

    def _get_ktb_email(self, pe_line):
        return (
            pe_line.payment_partner_id.email
            and pe_line.payment_partner_id.email[:40].ljust(40)
            or "".ljust(40)
        )

    def _get_ktb_sms(self, pe_line):
        return (
            pe_line.payment_partner_id.phone
            and pe_line.payment_partner_id.phone[:20].ljust(20)
            or "".ljust(20)
        )

    def _get_ktb_receiver_sub_branch_code(self, pe_line):
        return "0".zfill(4)

    def _get_text_header_ktb(self, payment_lines):
        ktb_company_id = self.ktb_company_id or "**Company ID on KTB is not config**"
        total_batch = len(payment_lines.ids)
        total_amount = sum(payment_lines.mapped("payment_amount"))
        total_batch_amount = payment_lines._get_amount_no_decimal(total_amount, 2)
        text = (
            "101{idx}006{total_batch_transaction}{total_batch_amount}"
            "{effective_date}C{receiver_no}{ktb_company_id}{space}\r\n".format(
                idx="1".zfill(6),  # 1 Batch = 1 File, How we can add more than 1 batch?
                total_batch_transaction=str(total_batch).zfill(7),
                total_batch_amount=str(total_batch_amount).zfill(19),
                effective_date=self.effective_date.strftime("%d%m%Y"),
                receiver_no="0".zfill(8),
                ktb_company_id=ktb_company_id.ljust(16),
                space="".ljust(427),  # user id and filter (20 + 407 char)
            )
        )
        return text

    def _get_text_body_ktb(self, idx, pe_line, payment_net_amount_bank):
        # Sender
        sender_name = self._get_ktb_sender_name()
        (
            sender_bank_code,
            sender_branch_code,
            sender_acc_number,
        ) = pe_line._get_sender_information()
        # Receiver
        (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        ) = pe_line._get_receiver_information()
        ktb_service_type = (
            self.ktb_bank_type == "standard"
            and self.ktb_service_type_standard
            or self.ktb_service_type_direct
        )
        text = (
            "102{idx}{receiver_bank_code}{receiver_branch_code}{receiver_acc_number}"
            "{sender_bank_code}{sender_branch_code}{sender_acc_number}"
            "{effective_date}{ktb_service_type}00{payment_net_amount_bank}"
            "{receiver_info}{receiver_id}{receiver_name}{sender_name}{other_info1}"
            "{ddr_ref1}{space}{ddr_ref2}{space}{other_info2}"
            "{ref_running_number}09{email}{sms}{receiver_sub_branch_code}"
            "{filter}\r\n".format(
                idx="1".zfill(6),  # 1 Batch = 1 File, How we can add more than 1 batch?
                receiver_bank_code=receiver_bank_code,  # 10-12
                receiver_branch_code=receiver_branch_code,  # 13-16
                receiver_acc_number=receiver_acc_number,  # 17-27
                sender_bank_code=sender_bank_code,  # 28-30
                sender_branch_code=sender_branch_code,  # 31-34
                sender_acc_number=sender_acc_number,  # 35-45
                effective_date=self.effective_date.strftime("%d%m%Y"),  # 46-53
                ktb_service_type=ktb_service_type,  # 54-55
                payment_net_amount_bank=payment_net_amount_bank  # 58-74
                and str(payment_net_amount_bank)[:17].zfill(17)
                or "0".zfill(17),
                receiver_info=self._get_ktb_receiver_info(pe_line),  # 75-82
                receiver_id=self._get_ktb_receiver_id(pe_line),  # 83-92
                receiver_name=receiver_name,  # 93-192
                sender_name=sender_name[:100].ljust(100),  # 193-292
                other_info1=self._get_ktb_other_info1(pe_line),  # 293-332
                ddr_ref1=self._get_ktb_ddr_ref1(pe_line),  # 333-350
                ddr_ref2=self._get_ktb_ddr_ref2(pe_line),  # 353-370
                space="".ljust(2),  # 351-352 and 371-372
                other_info2=self._get_ktb_other_info2(pe_line),  # 373-392
                ref_running_number=str(idx + 1).zfill(6),  # 393-398
                email=self._get_ktb_email(pe_line),  # 401-440
                sms=self._get_ktb_sms(pe_line),  # 441-460
                receiver_sub_branch_code=self._get_ktb_receiver_sub_branch_code(
                    pe_line
                ),  # 461-464
                filter="".ljust(34),
            )
        )
        return text

    def _format_ktb_text(self):
        total_amount = 0
        payment_lines = self.export_line_ids
        # Header
        text = self._get_text_header_ktb(payment_lines)
        # Details
        for idx, pe_line in enumerate(payment_lines):
            # This amount related decimal from invoice, Odoo invoice do not rounding.
            payment_net_amount = pe_line._get_payment_net_amount()
            payment_net_amount_bank = pe_line._get_amount_no_decimal(
                payment_net_amount, 2
            )
            text += self._get_text_body_ktb(idx, pe_line, payment_net_amount_bank)
            total_amount += payment_net_amount_bank
        return text

    def _generate_bank_payment_text(self):
        self.ensure_one()
        if self.bank == "KRTHTHBK":  # KTB
            return self._format_ktb_text()
        return super()._generate_bank_payment_text()

    def _get_view_report_text(self):
        if self.bank == "KRTHTHBK":
            return "l10n_th_bank_payment_export_ktb.action_payment_ktb_txt"
        return super()._get_view_report_text()

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
