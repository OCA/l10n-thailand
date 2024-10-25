# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentExport(models.Model):
    _inherit = "bank.payment.export"

    bank = fields.Selection(
        selection_add=[("TMBKTHBK", "TTB")],
        ondelete={"TMBKTHBK": "cascade"},
    )
    ttb_is_editable = fields.Boolean(
        compute="_compute_ttb_editable",
        string="TTB Editable",
    )
    ttb_transaction_code = fields.Selection(
        selection=[
            ("01", "01 - จ่ายเงินเดือน"),
            ("04", "04 - จ่ายค่าสินค้า / บริการ"),
            ("59", "59 - อื่นๆ"),
        ],
        string="Transaction Code",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ttb_transaction_type = fields.Selection(
        selection=[
            ("BNT", "BNT - BahtNet"),
            ("MCP", "MCP - Cheque Payment"),
            ("DCB", "DCB - Direct Credit (Next Day)"),
            ("DDB", "DDB - Direct Debit (Next Day)"),
            ("OAT", "OAT - Own Account Transfer"),
            ("PRS", "PRS - Payroll Staff"),
            ("PRM", "PRM - Payroll Management"),
            ("PBN", "PBN - PromptPay (Next Day)"),
            ("PBS", "PBS - PromptPay (Same Day)"),
            ("MCL", "MCL - SMART Payment"),
            ("PMN", "PMN - SMART Payroll Management (Next Day)"),
            ("PMS", "PMS - SMART Payroll Management (Same Day)"),
            ("PSN", "PSN - SMART Payroll Staff (Next Day)"),
            ("PSS", "PSS - SMART Payroll Staff (Same Day)"),
            ("SCS", "SCS - SMART Same Day"),
            ("COP", "COP - Cashier's Order Payment"),
        ],
        string="Transaction Type",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ttb_delivery_method = fields.Selection(
        selection=[
            ("OC", "OC - Counter"),
            ("MA", "MA - Mail"),
            ("RT", "RT - Return"),
            ("CR", "CR - Courier"),
        ],
        string="Delivery Method",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ttb_pickup_location = fields.Selection(
        selection=[
            ("PHAHONYOTHIN", "PHAHONYOTHIN"),
            ("BC-CHONBURI", "BC-CHONBURI"),
            ("BC-HADYAI", "BC-HADYAI"),
            ("BC-NAKHONRATCHASIMA", "BC-NAKHONRATCHASIMA"),
            ("BC-RANGSIT", "BC-RANGSIT"),
            ("BC-RAYONG", "BC-RAYONG"),
            ("BC-SAMUTSAKORN", "BC-SAMUTSAKORN"),
            ("BC-SARABURI", "BC-SARABURI"),
        ],
        string="Pickup Location",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ttb_document_required = fields.Char(
        string="Document(s) Required",
        size=30,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    ttb_payment_details = fields.Text(
        string="Payment Details",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.depends("bank")
    def _compute_ttb_editable(self):
        for export in self:
            export.ttb_is_editable = export.bank == "TMBKTHBK"

    def _get_ttb_wht_type_code(self, wht_line):
        mapping_wht_code = {
            "1": "11",
            "2": "21",
            "3": "31",
            "4A": "41",
            "4B11": "42",
            "4B12": "43",
            "4B13": "44",
            "4B14": "45",
            "4B21": "46",
            "4B22": "47",
            "5": "51",
            "6": "61",
        }
        return mapping_wht_code.get(wht_line.wht_cert_income_type, "")

    # @api.onchange("ktb_bank_type")
    # def _onchange_ktb_bank_type(self):
    #     if self.ktb_bank_type == "standard":
    #         self.ktb_service_type_direct = False
    #     else:
    #         self.ktb_service_type_standard = False

    @api.depends("bank")
    def _compute_required_effective_date(self):
        res = super()._compute_required_effective_date()
        for rec in self.filtered(lambda l: l.bank == "TMBKTHBK"):
            rec.is_required_effective_date = True
        return res

    # def _check_constraint_confirm(self):
    #     res = super()._check_constraint_confirm()
    #     for rec in self.filtered(lambda l: l.bank == "KRTHTHBK"):
    #         if not rec.ktb_bank_type:
    #             raise UserError(_("You need to add 'Bank Type' before confirm."))
    #         if rec.ktb_bank_type == "direct" and any(
    #             line.payment_bank_id.bic != rec.bank for line in rec.export_line_ids
    #         ):
    #             raise UserError(
    #                 _("Bank type '{}' can not export payment to other bank.").format(
    #                     dict(self._fields["ktb_bank_type"].selection).get(
    #                         self.ktb_bank_type
    #                     )
    #                 )
    #             )
    #         if rec.ktb_bank_type == "standard" and any(
    #             line.payment_bank_id.bic == rec.bank for line in rec.export_line_ids
    #         ):
    #             raise UserError(
    #                 _("Bank type '{}' can not export payment to the same bank.").format(
    #                     dict(self._fields["ktb_bank_type"].selection).get(
    #                         self.ktb_bank_type
    #                     )
    #                 )
    #             )
    #     return res

    # def _get_context_create_bank_payment_export(self, payments):
    #     ctx = super()._get_context_create_bank_payment_export(payments)
    #     partner_bic_bank = list(set(payments.mapped("partner_bank_id.bank_id.bic")))
    #     # KTB Bank
    #     if partner_bic_bank and ctx["default_bank"] == "KRTHTHBK":
    #         # Same bank
    #         if len(partner_bic_bank) == 1 and partner_bic_bank[0] == "KRTHTHBK":
    #             ctx.update({"default_ktb_bank_type": "direct"})
    #         # Other bank
    #         elif "KRTHTHBK" not in partner_bic_bank:
    #             ctx.update({"default_ktb_bank_type": "standard"})
    #     return ctx

    # def _check_constraint_line(self):
    #     # Add condition with line on this function
    #     res = super()._check_constraint_line()
    #     self.ensure_one()
    #     if self.bank == "KRTHTHBK":
    #         for line in self.export_line_ids:
    #             if not line.payment_partner_bank_id:
    #                 raise UserError(
    #                     _("Recipient Bank with {} is not selected.").format(
    #                         line.payment_id.name
    #                     )
    #                 )
    #     return res

    # def _check_constraint_create_bank_payment_export(self, payments):
    #     res = super()._check_constraint_create_bank_payment_export(payments)
    #     payment_bic_bank = list(set(payments.mapped("journal_id.bank_id.bic")))
    #     payment_bank = len(payment_bic_bank) == 1 and payment_bic_bank[0] or ""
    #     method_manual_out = self.env.ref("account.account_payment_method_manual_out")
    #     # Check case KTB must have 1 journal / 1 PE
    #     if payment_bank == "KRTHTHBK" and len(payments.mapped("journal_id")) > 1:
    #         raise UserError(
    #             _("KTB can create bank payment export 1 Journal / 1 Payment Export.")
    #         )
    #     for payment in payments:
    #         if (
    #             payment.payment_method_id.id != method_manual_out.id
    #             or payment.journal_id.type != "bank"
    #         ):
    #             raise UserError(
    #                 _(
    #                     "You can export bank payments with journal 'Bank' "
    #                     "and Payment method 'Manual' only"
    #                 )
    #             )
    #         if payment.company_id.currency_id != payment.currency_id:
    #             raise UserError(
    #                 _("Payments must be currency '{}' only").format(
    #                     payment.company_id.currency_id.name
    #                 )
    #             )
    #     return res
