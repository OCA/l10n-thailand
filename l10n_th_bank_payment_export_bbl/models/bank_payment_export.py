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
        help="""You can config this field from menu
            Invoicing > Configuration > Payments > Bank Payment Configuration""",
    )
    config_bbl_customer_batch_smart = fields.Many2one(
        comodel_name="bank.payment.config",
        string="BBL Customer Batch Smart",
        default=lambda self: self._default_common_config(
            "config_bbl_customer_batch_smart"
        ),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""You can config this field from menu
            Invoicing > Configuration > Payments > Bank Payment Configuration""",
    )
    config_bbl_customer_batch_direct = fields.Many2one(
        comodel_name="bank.payment.config",
        string="BBL Customer Batch Direct",
        default=lambda self: self._default_common_config(
            "config_bbl_customer_batch_direct"
        ),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="""You can config this field from menu
            Invoicing > Configuration > Payments > Bank Payment Configuration""",
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
        help="""This field can config from company contact 2 ways following,
            1. Go to menu Settings > Users & Companies > Companies
                - Select your company > Contact > Invoicing
                - Add new Bank Accounts
            2. Go to menu Contacts
                - Select your company > Contact > Invoicing
                - Add new Bank Accounts""",
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

    def _hook_batch_broadcast_message(self):
        """Message code maintained in C@W used for batch transactions.
        Based on this message code, Cash@Will will broadcast against this customer
        reference number at the time of payment initiation."""
        return  ""
    
    def _hook_value_time_7(self):
        """This time is used for crediting the Beneficiary.
        If nothing is specified, then credit will happen at next cycle.
        The format is HH24MISS"""
        return  ""
    
    def _hook_pre_advice_date_10(self):
        """Date of notification to the Beneficiary.
        The format for this date is DDMMYYYY"""
        return  ""
    
    def _hook_wht_22_25(self, pe_line, wht, index):
        """WHT Bank Payment Export"""
        # NOTE: Not test with multi wht in 1 payment.
        if index == 22:
            return wht.wht_cert_income_type
        elif index == 23:
            return "001"  # TODO: 23 - 25 For test
        elif index == 25:
            return  ""
    
    def _hook_bathnet_type_code_26(self):
        """This will contain BahtNet service code for BahtNet product.
        Details of same will be provided by BBL team"""
        return  ""
    
    def _hook_wht_no_28(self):
        """Indicates number of WHT for particular transaction"""
        return  "" # TODO: do something
    
    def _hook_wht_amount_29(self):
        """Indicates Total WHT Amount for particular transaction.
        Divide by 100 for actual value"""
        return  "" # TODO: do something
    
    def _hook_invoice_no_30(self):
        """Indicates number of Invoice for particular transaction"""
        return  ""
    
    def _hook_total_invoice_amount_31(self):
        """Indicates Total Invoice Amount for particular transaction.
        Divide by 100 for actual value"""
        return  ""
    
    def _hook_total_discount_amount_32(self):
        """Indicates Total Discount Amount for particular transaction.
        Divide by 100 for actual value"""
        return  ""
    
    def _hook_wht_pay_type_35(self):
        """Will have values "01" - "04". This will be passed to C@W as is"""
        return  "" # TODO: do something

    def _hook_wht_remark_36(self):
        """If Paid Tax Type is '04' then file will have this description"""
        return  "" # TODO: do something
    
    def _hook_wht_deduct_date_37(self):
        return  "" # TODO: do something
    
    def _hook_wht_signatory_40(self):
        """This will have values "B" for Bank or "C" for Customer"""
        return  "" # TODO: do something
    
    def _hook_service_code_41(self):
        """This is service code used by corporate customer categorize
        different departments. This shall be maintained in C@W"""
        return ""
    
    def _hook_beneficiary_code_42(self):
        """This is beneficiary code maintained in the system.
        If this customer is maintained for Pre-Registered beneficiary,
        then system will fetch Beneficiary details from Beneficiary Setup
        and corresponding following details will be ignored. In that case this will"""
        return ""
    
    def _hook_payee_address(self, receiver_name, index):
        """Beneficiary Address 1 - 4"""
        return ""
    
    def _hook_dispatch_address(self, receiver_name, index):
        """Dispatch Address 1 - 4"""
        return ""
    
    def _hook_payee_fax_54(self):
        """Fax number used to send FAX. If Alert Notification via FAX,
        then Fax number is mandatory. No comma allow in this field."""
        return ""
    
    def _hook_payee_mobile_55(self):
        """Mobile number used to send SMS. If Alert Notification via mobile phone,
        then Mobile Number is mandatory"""
        return ""
    
    def _hook_credit_sequence_3(self):
        """Unique running serial number"""
        return ""
    
    def _hook_ewht_income_type_5(self):
        """Refer to Domestic E-WHT Income Type Code."""
        return  "" # TODO: do something

    def _get_text_header_bbl(self, company_code):
        self.ensure_one()
        customer_batch_ref = (
            self.bbl_bank_type == "smart"
            and self.config_bbl_customer_batch_smart.value
            or self.config_bbl_customer_batch_direct.value
        )
        now_tz = fields.Datetime.context_timestamp(
            self.env["res.users"], datetime.now()
        )
        text = (
            "001~{company_code_2}~{company_tax_3}~{bbl_company_bank_account_4}~"
            "{customer_batch_ref_5}~{batch_broadcast_message_6}~{file_date_7}~"
            "{file_timestamp_8}\n".format(
                company_code_2=company_code,
                company_tax_3=self.env.company.vat or "**Company Tax is not config**",
                bbl_company_bank_account_4=self.bbl_company_bank_account.acc_number,
                customer_batch_ref_5=customer_batch_ref
                or "**Customer Batch Reference is not config**",
                batch_broadcast_message_6=self._hook_batch_broadcast_message(),  # optional
                file_date_7=now_tz.strftime("%d%m%Y"),
                file_timestamp_8=now_tz.strftime("%H%M%S"),
            )
        )
        return text

    def _get_text_body_detail_bbl(self, idx, pe_line, company_code, payment_net_amount_bank, bbl_ewht, wht):
        # Receiver
        (
            receiver_name,
            receiver_bank_code,
            receiver_branch_code,
            receiver_acc_number,
        ) = pe_line._get_receiver_information()
        text = (
            "003~{company_code_2}~{sequence_3}~{bbl_product_code_4}~"
            "{receiver_acc_number_5}~{value_date_6}~{value_time_7}~{currency_8}~"
            "{internal_ref_9}~{pre_advice_date_10}~~~~~~~~~{bbl_credit_advice_19}"
            "~~~{wht_form_type_22}~{wht_serial_no_23}~~{wht_running_no_25}~"
            "{bathnet_type_code_26}~{bbl_bot_type_27}~{wht_no_28}~{wht_amount_29}~"
            "{invoice_no_30}~{total_invoice_amount_31}~{total_discount_amount_32}~"
            "{bbl_payee_charge_33}~{payment_net_amount_34}~{wht_pay_type_35}~"
            "{wht_remark_36}~{wht_deduct_date_37}~{receiver_bank_code_38}~"
            "{receiver_branch_code_39}~{wht_signatory_40}~{service_code_41}~"
            "{beneficiary_code_42}~~{payee_name_44}~{payee_address1_45}~"
            "{payee_address2_46}~{payee_address3_47}~{payee_address4_48}~"
            "{dispatch_address1_49}~{dispatch_address2_50}~{dispatch_address3_51}~"
            "{dispatch_address4_52}~{payee_tax_53}~{payee_fax_54}~{payee_mobile_55}~"
            "{payee_email_56}\n".format(
                company_code_2=company_code,
                sequence_3=idx,
                bbl_product_code_4=self.bbl_product_code,
                receiver_acc_number_5=receiver_acc_number,
                value_date_6=pe_line.payment_date.strftime("%d%m%Y"),
                value_time_7=self._hook_value_time_7(),  # optional
                currency_8=pe_line.currency_id.name,
                internal_ref_9=pe_line.payment_id.name,
                pre_advice_date_10=self._hook_pre_advice_date_10(),  # optional
                # NOTE: 11 - 18 For Chq Pmt only, this module not support.
                bbl_credit_advice_19=self.bbl_credit_advice and "Y" or "N",
                # NOTE: 20 - 21 For Chq Pmt only, this module not support.
                wht_form_type_22=bbl_ewht and self._hook_wht_22_25(pe_line, wht, 22) or "",
                wht_serial_no_23=bbl_ewht and self._hook_wht_22_25(pe_line, wht, 23) or "",
                # NOTE: 24 is Book No., Not support
                wht_running_no_25=bbl_ewht and self._hook_wht_22_25(pe_line, wht, 25) or "",
                bathnet_type_code_26=self._hook_bathnet_type_code_26(),  # TODO: eWHT?
                bbl_bot_type_27=self.bbl_bot_type,
                wht_no_28=bbl_ewht and self._hook_wht_no_28() or "",
                wht_amount_29=bbl_ewht and self._hook_wht_amount_29() or "",
                invoice_no_30=self._hook_invoice_no_30(),  # optional
                total_invoice_amount_31=self._hook_total_invoice_amount_31(),  # optional
                total_discount_amount_32=self._hook_total_discount_amount_32(),  # optional
                bbl_payee_charge_33=self.bbl_payee_charge,
                payment_net_amount_34=payment_net_amount_bank
                and str(payment_net_amount_bank).zfill(16)
                or "0".zfill(16),
                wht_pay_type_35=bbl_ewht and self._hook_wht_pay_type_35() or "",
                wht_remark_36=bbl_ewht and self._hook_wht_remark_36() or "",
                wht_deduct_date_37=bbl_ewht and self._hook_wht_deduct_date_37() or "",
                receiver_bank_code_38=receiver_bank_code,
                receiver_branch_code_39=receiver_branch_code,
                wht_signatory_40=bbl_ewht and self._hook_wht_signatory_40() or "",
                service_code_41=self._hook_service_code_41(),  # optional
                beneficiary_code_42=self._hook_beneficiary_code_42(),  # optional
                # NOTE: 43 For Chq Pmt only, this module not support.
                payee_name_44=receiver_name,
                payee_address1_45=self._hook_payee_address(receiver_name, 45),  #optional
                payee_address2_46=self._hook_payee_address(receiver_name, 46),  #optional
                payee_address3_47=self._hook_payee_address(receiver_name, 47),  #optional
                payee_address4_48=self._hook_payee_address(receiver_name, 48),  #optional
                dispatch_address1_49=self._hook_dispatch_address(receiver_name, 49),  # optional
                dispatch_address2_50=self._hook_dispatch_address(receiver_name, 50),  # optional
                dispatch_address3_51=self._hook_dispatch_address(receiver_name, 51),  # optional
                dispatch_address4_52=self._hook_dispatch_address(receiver_name, 52),  # optional
                payee_tax_53=bbl_ewht and pe_line.payment_id.partner_id.vat or "",
                payee_fax_54=self._hook_payee_fax_54(),  # optional
                payee_mobile_55=self._hook_payee_mobile_55(),  # optional
                payee_email_56=bbl_ewht and pe_line.payment_id.partner_id.email or "",
            )
        )
        return text
    
    def _get_text_body_wht_bbl(self, pe_line, wht):
        text = (
            "005~{internal_ref_2}~{credit_sequence_3}~{wht_amount_4}~"
            "{ewht_income_type_5}~{wht_rate_6}~{income_type_amount_7}".format(
                internal_ref_2=pe_line.payment_id.name,
                credit_sequence_3=self._hook_credit_sequence_3(),  # optional
                wht_amount_4=wht.amount_wht,
                ewht_income_type_5=self._hook_ewht_income_type_5(),
                wht_rate_6=0,  # TODO: how to find percent if many lines?
                income_type_amount_7=0  # TODO: invoice or payment?
            )
        )
        return

    def _get_text_footer_bbl(self, total_amount, payment_lines):
        text = "100~{len_payment}~{total_amount}".format(
            len_payment=len(payment_lines.ids),
            total_amount=total_amount,
        )
        return text

    def _format_bbl_text(self):
        self.ensure_one()
        company_code = (
            self.config_bbl_company_code.value or "**Company Code is not config**"
        )
        # export with eWHT
        bbl_ewht = self.env.company.bbl_config_ewht
        wht = False
        total_amount = 0
        # Header - 001
        text = self._get_text_header_bbl(company_code)
        payment_lines = self.export_line_ids
        for idx, pe_line in enumerate(payment_lines):
            # Find table wht on payment
            if bbl_ewht:
                wht = pe_line.payment_id.wht_move_ids.filtered(lambda l: not l.is_pit)
            # This amount related decimal from invoice, Odoo invoice do not rounding.
            payment_net_amount = pe_line._get_payment_net_amount()
            payment_net_amount_bank = int(payment_net_amount * 100)
            # Details - 003
            text += self._get_text_body_detail_bbl(
                idx + 1, pe_line, company_code, payment_net_amount_bank, bbl_ewht, wht
            )
            # Details - 005 (eWHT)
            if bbl_ewht and wht:
                text += self._get_text_body_wht_bbl(pe_line, wht)
            total_amount += payment_net_amount_bank
        # Footer - 100
        text += self._get_text_footer_bbl(total_amount, payment_lines)
        return text

    def _generate_bank_payment_text(self):
        self.ensure_one()
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
