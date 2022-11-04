# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_round


class BankPaymentExportLine(models.Model):
    _name = "bank.payment.export.line"
    _description = "Bank Payment Export File"

    payment_export_id = fields.Many2one(
        comodel_name="bank.payment.export",
        index=True,
    )
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        required=True,
        domain=lambda self: self.payment_export_id._domain_payment_id(),
        ondelete="restrict",
        index=True,
    )
    payment_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="payment_id.journal_id",
        string="Journal",
    )
    payment_partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="payment_id.partner_id",
        string="Vendor",
    )
    payment_partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank",
        compute="_compute_payment_default",
        string="Recipient Bank",
        store=True,
        index=True,
        states={"draft": [("readonly", False)]},
    )
    payment_bank_id = fields.Many2one(
        comodel_name="res.bank",
        related="payment_partner_bank_id.bank_id",
        string="Bank",
        store=True,
        index=True,
    )
    payment_date = fields.Date(related="payment_id.date")
    payment_amount = fields.Monetary(related="payment_id.amount")
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="payment_id.currency_id",
        store=True,
    )
    state = fields.Selection(
        related="payment_export_id.state",
        string="Status",
        store=True,
    )

    _sql_constraints = [
        (
            "export_product_uniq",
            "unique(payment_export_id, payment_id)",
            "Duplicate payment in transaction not allowed!",
        )
    ]

    @api.depends("payment_id")
    def _compute_payment_default(self):
        for rec in self:
            rec.payment_partner_bank_id = rec.payment_id.partner_bank_id or False

    def clear_payment_exported(self):
        return self.mapped("payment_id").write(
            {
                "export_status": "draft",
                "payment_export_id": False,
            }
        )

    def _action_reject_bank_payment(self):
        return self.payment_export_id.action_reject()

    def action_reject(self):
        self.clear_payment_exported()
        self.write({"state": "reject"})
        lines_not_reject = self.payment_export_id.export_line_ids.filtered(
            lambda l: l.state != "reject"
        )
        # all line rejected, it should auto reject header too.
        if not lines_not_reject:
            self._action_reject_bank_payment()
        return True

    @api.model
    def create(self, vals):
        """link payment and bank payment export"""
        export_line = super().create(vals)
        export_line.payment_id.write(
            {
                "export_status": "to_export",
                "payment_export_id": vals["payment_export_id"],
            }
        )
        return export_line

    def unlink(self):
        """Check state draft can delete only."""
        self.clear_payment_exported()
        return super().unlink()

    # ====================== Function Common Text File ======================

    def _get_payment_net_amount(self):
        # TODO: Not support multi-currency
        # payment_net_amount = self.currency_id._convert(
        #     self.payment_amount,
        #     self.payment_id.company_id.currency_id,
        #     self.payment_id.company_id,
        #     self.payment_date,
        #     round=False,
        # )
        payment_net_amount = self.payment_amount
        return payment_net_amount

    def _get_amount_no_decimal(self, amount):
        return int(round(float_round(amount * 100, precision_rounding=1), 2))

    def _get_acc_number_digit(self, partner_bank_id):
        acc_number = partner_bank_id.acc_number
        if not acc_number:
            return "**receiver account number is null**"
        if len(acc_number) <= 11:
            return acc_number.zfill(11)
        # BAAC: ธ. เพื่อการเกษตรและสหกรณ์การเกษตร
        # HSBC: ธ. ฮ่องกงและเซี่ยงไฮ้แบงกิ้งคอร์ปอเรชั่น จำกัด
        if partner_bank_id.bank_id.bic in ("BAABTHBK", "HSBCTHBK"):
            return (
                len(acc_number) == 12
                and acc_number[1:]
                or "**Digit account number is not correct**"
            )
        # TISCO: ธ. ทิสโก้ จำกัด (มหาชน)
        # KKP: ธ. เกียรตินาคิน จำกัด (มหาชน)
        if partner_bank_id.bank_id.bic in ("TFPCTHB1", "KKPBTHBK"):
            return (
                len(acc_number) == 14
                and acc_number[4:].zfill(11)
                or "**Digit account number is not correct**"
            )
        # IBANK: ธ. อิสลามแห่งประเทศไทย (For 12 digits)
        if partner_bank_id.bank_id.bic == "TIBTTHBK":
            return (
                len(acc_number) == 12
                and acc_number[2:].zfill(11)
                or "**Digit account number is not correct**"
            )
        # GSB: ธ. ออมสิน
        if partner_bank_id.bank_id.bic == "GSBATHBK":
            if len(acc_number) == 12:
                acc_number = "".join(["999", acc_number])
            return (
                len(acc_number) == 15
                and acc_number[4:]
                or "**Digit account number is not correct**"
            )
        return acc_number

    def _get_receiver_information(self):
        self.ensure_one()
        partner_bank_id = self.payment_partner_bank_id
        receiver_name = (
            partner_bank_id.acc_holder_name or partner_bank_id.partner_id.display_name
        )
        receiver_bank_code = (
            partner_bank_id.bank_id.bank_code or "**receiver bank code is null**"
        )
        receiver_branch_code = (
            partner_bank_id.bank_id.bank_branch_code
            or "**receiver branch code is null**"
        )
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
        sender_bank_code = (
            sender_journal_id.bank_id.bank_code or "**sender bank code is null**"
        )
        sender_branch_code = (
            sender_journal_id.bank_id.bank_branch_code
            or "**sender branch code is null**"
        )
        sender_acc_number = (
            sender_journal_id.bank_account_id.acc_number
            or "**sender account number is null**"
        )
        return sender_bank_code, sender_branch_code, sender_acc_number
