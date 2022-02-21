# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BankPaymentExport(models.Model):
    _inherit = "bank.payment.export"

    bank = fields.Selection(
        selection_add=[("BKKBTHBK", "BBL")],
        ondelete={"BKKBTHBK": "cascade"},
    )
    # Configuration
    config_bbl_company_code = fields.Many2one(
        comodel_name="bank.payment.config",
        string="BBL Company Code",
        default=lambda self: self._default_common_config("config_bbl_company_code"),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""
            You can config this field from menu
            Invoicing > Configuration > Payments > Bank Payment Configuration
        """,
    )
    config_bbl_customer_batch_smart = fields.Many2one(
        comodel_name="bank.payment.config",
        string="BBL Customer Batch Smart",
        default=lambda self: self._default_common_config(
            "config_bbl_customer_batch_smart"
        ),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""
            You can config this field from menu
            Invoicing > Configuration > Payments > Bank Payment Configuration
        """,
    )
    config_bbl_customer_batch_direct = fields.Many2one(
        comodel_name="bank.payment.config",
        string="BBL Customer Batch Direct",
        default=lambda self: self._default_common_config(
            "config_bbl_customer_batch_direct"
        ),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""
            You can config this field from menu
            Invoicing > Configuration > Payments > Bank Payment Configuration
        """,
    )
    # filter
    bbl_is_editable = fields.Boolean(
        compute="_compute_bbl_editable",
        string="BBL Editable",
    )
    bbl_bank_type = fields.Selection(
        selection=[
            ("direct", "Direct"),
            ("smart", "Smart"),
        ],
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    bbl_company_bank_account = fields.Many2one(
        comodel_name="res.partner.bank",
        string="Company Bank Account",
        domain=lambda self: self._get_account_number_company_domain(),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    bbl_payee_charge = fields.Selection(
        selection=[("OUR", "Payer"), ("BEN", "Beneficiary")],
        ondelete={"OUR": "cascade", "BEN": "cascade"},
        string="Payee Charge",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    bbl_credit_advice = fields.Boolean(
        string="Credit Advice",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    bbl_product_code = fields.Selection(
        selection=[
            ("DCB01", "Direct Credit Bank Period"),
            ("DCB02", "Direct Credit Bank Immediately"),
            ("SMC04", "Smart Credit Same Day"),
            ("SMC06", "Smart Credit Next Day"),
        ],
        ondelete={
            "DCB01": "cascade",
            "DCB02": "cascade",
            "SMC04": "cascade",
            "SMC06": "cascade",
        },
        string="Product Code",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    bbl_bot_type = fields.Selection(
        selection=[
            ("01", "Salary Wage Pension"),
            ("02", "Dividend"),
            ("03", "Interests"),
            ("04", "Good and Service"),
            ("05", "Selling Securities"),
            ("07", "Loan"),
            ("59", "Credit ONLY - Others"),
        ],
        ondelete={
            "01": "cascade",
            "02": "cascade",
            "03": "cascade",
            "04": "cascade",
            "05": "cascade",
            "07": "cascade",
            "59": "cascade",
        },
        string="BOT service type of payment",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.depends("bank")
    def _compute_bbl_editable(self):
        for export in self:
            export.bbl_is_editable = False
            if export.bank == "BKKBTHBK":
                export.bbl_is_editable = True

    @api.depends("bank")
    def _compute_required_effective_date(self):
        super()._compute_required_effective_date()
        for rec in self.filtered(lambda l: l.bank == "BKKBTHBK"):
            rec.is_required_effective_date = False

    @api.model
    def _get_account_number_company_domain(self):
        return [("partner_id", "=", self.env.company.id)]

    @api.onchange("bbl_product_code")
    def onchange_bbl_product_code(self):
        if self.bank == "BKKBTHBK" and self.bbl_product_code:
            match_direct = re.search("DCB.+", self.bbl_product_code)
            match_smart = re.search("SMC.+", self.bbl_product_code)
            self.bbl_bank_type = (
                match_direct and "direct" or (match_smart and "smart") or ""
            )

    def action_done(self):
        res = super().action_done()
        if self.bank == "BKKBTHBK":
            self.effective_date = fields.Date.context_today(self)
        return res

    def _get_text_header_bbl(self, company_code):
        customer_batch_ref = (
            self.bbl_bank_type == "smart"
            and self.config_bbl_customer_batch_smart.value
            or self.config_bbl_customer_batch_direct.value
        )
        now_tz = fields.Datetime.context_timestamp(
            self.env["res.users"], datetime.now()
        )
        text = (
            "001~{company_code}~{company_tax}~{bbl_company_bank_account}~"
            "{customer_batch_ref}~~{file_date}~{file_timestamp}\n".format(
                company_code=company_code,
                company_tax=self.env.company.vat or "**Company Tax is not config**",
                bbl_company_bank_account=self.bbl_company_bank_account.acc_number,
                customer_batch_ref=customer_batch_ref
                or "**Customer Batch Reference is not config**",
                file_date=now_tz.strftime("%d%m%Y"),
                file_timestamp=now_tz.strftime("%H%M%S"),
            )
        )
        return text

    def _get_text_body_bbl(self, idx, pe_line, company_code, payment_net_amount_bank):
        # Receiver
        (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        ) = pe_line._get_receiver_information()
        text = (
            "003~{company_code}~{sequence}~{bbl_product_code}~"
            "{receiver_acc_number}~{value_date}~~{currency}~{internal_ref}~~~~~~~~~~"
            "{bbl_credit_advice}~~~~~~~~{bbl_bot_type}~~~~~~{bbl_payee_charge}~"
            "{payment_net_amount}~~~~{receiver_bank_code}~"
            "{receiver_branch_code}~~~~~{receiver_name}~~~~~~~~~~~~\n".format(
                company_code=company_code,
                sequence=idx,
                bbl_product_code=self.bbl_product_code,
                receiver_acc_number=receiver_acc_number.zfill(11),
                value_date=pe_line.payment_date.strftime("%d%m%Y"),
                currency=pe_line.currency_id.name,
                internal_ref=pe_line.payment_id.name,
                bbl_credit_advice=self.bbl_credit_advice and "Y" or "N",
                bbl_bot_type=self.bbl_bot_type,
                bbl_payee_charge=self.bbl_payee_charge,
                payment_net_amount=payment_net_amount_bank
                and str(payment_net_amount_bank).zfill(16)
                or "0".zfill(16),
                receiver_bank_code=receiver_bank_code,
                receiver_branch_code=receiver_branch_code,
                receiver_name=receiver_name,
            )
        )
        return text

    def _get_text_footer_bbl(self, total_amount, payment_lines):
        text = "100~{len_payment}~{total_amount}".format(
            len_payment=len(payment_lines.ids),
            total_amount=total_amount,
        )
        return text

    def _format_bbl_text(self):
        company_code = (
            self.config_bbl_company_code.value or "**Company Code is not config**"
        )
        total_amount = 0
        # Header
        text = self._get_text_header_bbl(company_code)
        payment_lines = self.export_line_ids
        for idx, pe_line in enumerate(payment_lines):
            # This amount related decimal from invoice, Odoo invoice do not rounding.
            payment_net_amount = pe_line._get_payment_net_amount()
            payment_net_amount_bank = int(payment_net_amount * 100)
            # Details
            text += self._get_text_body_bbl(
                idx + 1, pe_line, company_code, payment_net_amount_bank
            )
            total_amount += payment_net_amount_bank
        # Footer
        text += self._get_text_footer_bbl(total_amount, payment_lines)
        return text

    def _generate_bank_payment_text(self):
        if self.bank == "BKKBTHBK":  # BBL
            return self._format_bbl_text()
        return super()._generate_bank_payment_text()

    def _get_view_report_text(self):
        if self.bank == "BKKBTHBK":
            return "l10n_th_bank_payment_export_bbl.action_payment_bbl_txt"
        return super()._get_view_report_text()

    def _check_constraint_confirm(self):
        res = super()._check_constraint_confirm()
        for rec in self.filtered(lambda l: l.bank == "BKKBTHBK"):
            if rec.bbl_bank_type == "direct" and any(
                line.payment_bank_id.bic != rec.bank for line in rec.export_line_ids
            ):
                raise UserError(
                    _(
                        "Bank type '{}' can not export payment to other bank.".format(
                            dict(self._fields["bbl_bank_type"].selection).get(
                                self.bbl_bank_type
                            )
                        )
                    )
                )
        return res
