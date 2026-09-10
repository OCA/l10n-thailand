# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import ROUND_HALF_UP, Decimal

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

    def _kbank_satang(self, amount):
        return str(
            int(
                (Decimal(str(amount)) * 100).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
        )

    def _set_global_dict(self):
        values = super()._set_global_dict()
        if self.bank == "KASITHBK":
            values["lines"] = self.export_line_ids.filtered(
                lambda line: line.state != "reject"
            )
        return values

    def _kbank_wht_lines(self, payment):
        certs = payment.wht_cert_ids.filtered(lambda cert: cert.state != "cancel")
        if self.kbank_transfer_type == "same_bank" and self.kbank_product_type == "FTR":
            return self.env["withholding.tax.cert.line"]
        return certs.mapped("wht_line")

    def _kbank_has_sms(self, payment, wht_lines):
        if not payment.partner_id.kbank_sms:
            return False
        if self.kbank_transfer_type == "same_bank":
            return self.kbank_product_type in ("FTL", "DCT") or (
                self.kbank_product_type == "PCT" and bool(wht_lines)
            )
        return self.kbank_payment_type != "PCL" or bool(wht_lines)

    def _get_data_level_payment(self, active_lines, parent_ctx):
        items = super()._get_data_level_payment(active_lines, parent_ctx)
        if self.bank != "KASITHBK":
            return items
        for ctx in items:
            payment = ctx["payment"]
            wht_lines = self._kbank_wht_lines(payment)
            # FTR/FTL use Invoice totals; DCT/PCT and other-bank products use WHT.
            invoice_totals = self.kbank_transfer_type == "same_bank" and (
                self.kbank_product_type == "FTR"
                or (self.kbank_product_type == "FTL" and wht_lines)
            )
            invoices = payment.reconciled_bill_ids
            ctx.update(
                kbank_wht_lines=wht_lines,
                kbank_totals={
                    "base": (
                        sum(invoices.mapped("amount_untaxed"))
                        if invoice_totals
                        else sum(wht_lines.mapped("base"))
                    ),
                    "tax": sum(wht_lines.mapped("amount")),
                    "after_vat": (
                        sum(invoices.mapped("amount_total")) if invoice_totals else 0
                    ),
                },
            )
        return items

    def _get_data_level_wht(self, active_lines, parent_ctx):
        if self.bank != "KASITHBK":
            return super()._get_data_level_wht(active_lines, parent_ctx)
        contexts = (
            [parent_ctx]
            if parent_ctx.get("payment")
            else (self._get_data_level_payment(active_lines, {}))
        )
        return [
            dict(ctx, wht_cert=wht.cert_id, kbank_wht_line=wht, idx_wht=idx)
            for ctx in contexts
            for idx, wht in enumerate(ctx["kbank_wht_lines"])
        ]

    def _kbank_payee_account(self, payment):
        account = self.export_line_ids.sanitize_account_number(
            payment.partner_bank_id.acc_number
        )
        if self.kbank_payment_type in ("BNL", "IPP"):
            return account.ljust(20)
        return account.zfill(20)

    def _kbank_branch(self, payment):
        bank = payment.partner_bank_id.bank_id
        code = (bank.bank_code or "").zfill(3)
        account = self.export_line_ids.sanitize_account_number(
            payment.partner_bank_id.acc_number
        )
        branch = (bank.bank_branch_code or "").strip()
        # Module1 overrides the Bank_Code table for these products.
        if self.kbank_payment_type == "IPP" and not branch:
            return "9999"
        if code == "030" and len(account) == 12 and self.kbank_payment_type != "IPP":
            return "9990"
        if branch:
            return branch
        fixed = {
            "008": "0001",
            "017": "0001",
            "018": "0001",
            "026": "0001",
            "027": "0001",
            "031": "0001",
            "032": "0001",
            "034": "0000",
            "039": "0001",
            "045": "0010",
            "052": "0001",
            "080": "0001",
        }
        if code in fixed:
            return fixed[code]
        if code in ("030", "067", "069", "073"):
            return account[:4]
        if code == "066" and len(account) == 12:
            return account[2:5] + " "
        return account[:3] + " "

    def _check_constraint_line(self):
        result = super()._check_constraint_line()
        if self.bank != "KASITHBK":
            return result
        if not self.effective_date or not self.kbank_charge_bearer:
            raise ValidationError(
                self.env._("Set the effective date and charge bearer.")
            )
        product = (
            self.kbank_product_type
            if self.kbank_transfer_type == "same_bank"
            else self.kbank_payment_type
        )
        if not product:
            raise ValidationError(self.env._("Select the KBank transfer product."))
        lines = self.export_line_ids.filtered(lambda line: line.state != "reject")
        accounts = lines.mapped("payment_journal_id.bank_account_id")
        if (
            not lines
            or len(accounts) != 1
            or any(not line.payment_journal_id.bank_account_id for line in lines)
        ):
            raise ValidationError(
                self.env._("Use one debit bank account per KBank file.")
            )
        debit = lines.sanitize_account_number(accounts.acc_number)
        if len(debit) != 10 or not debit.isascii() or not debit.isdigit():
            raise ValidationError(
                self.env._("The KBank debit account must have 10 digits.")
            )
        for line in lines:
            payment = line.payment_id
            account = line.sanitize_account_number(payment.partner_bank_id.acc_number)
            max_length = 10 if self.kbank_transfer_type == "same_bank" else 20
            if (
                not account
                or len(account) > max_length
                or (max_length == 10 and len(account) != 10)
            ):
                raise ValidationError(
                    self.env._("Invalid KBank payee account: %s", account)
                )
            if self.kbank_transfer_type == "other_bank":
                code = payment.partner_bank_id.bank_id.bank_code or ""
                if not code.isascii() or not code.isdigit() or len(code) > 3:
                    raise ValidationError(self.env._("Set a valid payee bank code."))
            if payment.amount <= 0:
                raise ValidationError(
                    self.env._("KBank payment amounts must be positive.")
                )
            wht_lines = self._kbank_wht_lines(payment)
            if len(wht_lines) > 3:
                raise ValidationError(
                    self.env._("KBank supports at most 3 WHT rows per payment.")
                )
            for cert in wht_lines.mapped("cert_id"):
                if not cert.income_tax_form:
                    raise ValidationError(self.env._("Set the WHT income tax form."))
            partner = payment.partner_id
            if self._kbank_has_sms(payment, wht_lines) and not partner.kbank_sms_lang:
                raise ValidationError(
                    self.env._("Set the KBank SMS language for %s.", partner.name)
                )
        return result

    def _generate_bank_payment_text(self):
        if self.bank == "KASITHBK":
            self._check_constraint_line()
        return super()._generate_bank_payment_text()
