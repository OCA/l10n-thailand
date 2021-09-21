# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from odoo import fields, models


class ExportBankPayment(models.TransientModel):
    _inherit = "export.bank.payment"

    bank = fields.Selection(
        selection_add=[("bbl", "BBL")],
        ondelete={"bbl": "cascade"},
    )

    def _get_text_header_bbl_smart(self, company_code):
        icp = self.env["ir.config_parameter"].sudo()
        customer_batch_ref = icp.get_param("export.payment.bbl.customer_batch_ref")
        now_tz = fields.Datetime.context_timestamp(
            self.env["res.users"], datetime.now()
        )
        company_id = self.env.company
        company_account = company_id.partner_id.bank_ids and\
            company_id.partner_id.bank_ids[0].acc_number
        text = (
            "001~{company_code}~{company_tax}~{company_account}~"
            "{customer_batch_ref}~~{file_date}~{file_timestamp}\n".format(
                company_code=company_code or "",
                company_tax=company_id.vat or "",
                company_account=company_account or "",
                customer_batch_ref=customer_batch_ref or "",
                file_date=now_tz.strftime("%d%m%Y"),
                file_timestamp=now_tz.strftime("%H%M%S"),
            )
        )
        return text

    def _get_text_body_bbl_smart(
        self, idx, payment, company_code, payment_net_amount_bank
    ):
        acc_number = payment.partner_bank_id.acc_number or False
        bank_code = payment.partner_bank_id.bank_id.bank_code or False
        bank_branch_code = payment.partner_bank_id.bank_id.bank_branch_code or False
        # This amount related decimal from invoice, Odoo invoice do not rounding.
        text = (
            "003~{company_code}~{sequence}~{product_code}~"
            "{account_number}~{value_date}~{currency}~~~~~~~~~~"
            "{credit_advice}~~~~~~~{bot_service}~~~~~{payee_charge}~"
            "{payment_net_amount}~~~~006~{received_bank_code}~"
            "{received_branch_code}~~~~~{payee_name}~~~~~~~~~~~~"
            "{payee_email}\n".format(
                company_code=company_code,
                sequence=idx,
                product_code="SMC06",
                account_number=acc_number and acc_number.zfill(11) or "",
                value_date=payment.date.strftime("%d%m%Y"),
                currency=payment.company_id.currency_id.name,
                credit_advice="N",
                bot_service="04",
                payee_charge="OUR",
                payment_net_amount=payment_net_amount_bank,
                received_bank_code=bank_code or "",
                received_branch_code=bank_branch_code or "",
                payee_name=payment.partner_id.display_name,
                payee_email="",
            )
        )
        return text

    def _get_text_footer_bbl_smart(self, total_amount):
        text = "100~{len_payment}~{total_amount}".format(
            len_payment=len(self.payment_ids),
            total_amount=total_amount,
        )
        return text

    def _format_bbl_smart_text(self):
        icp = self.env["ir.config_parameter"].sudo()
        company_code = icp.get_param("export.payment.bbl.company_code")
        total_amount = 0
        # Header
        text = self._get_text_header_bbl_smart(company_code)
        for idx, payment in enumerate(self.payment_ids):
            payment_net_amount = payment.currency_id._convert(
                payment.amount,
                payment.company_id.currency_id,
                payment.company_id,
                payment.date,
                round=False,
            )
            payment_net_amount_bank = int(payment_net_amount * 100)
            text += self._get_text_body_bbl_smart(
                idx, payment, company_code, payment_net_amount_bank
            )
            total_amount += payment_net_amount_bank
        # Footer
        text += self._get_text_footer_bbl_smart(total_amount)
        return text

    def _generate_bank_payment_text(self):
        if self.bank == "bbl" and self.type == "smart":
            return self._format_bbl_smart_text()
        return

    def _get_view_report_text(self):
        if self.bank == "bbl" and self.type == "smart":
            return "l10n_th_export_payment_bbl.action_payment_bbl_smart_txt"
        return super()._get_view_report_text()
