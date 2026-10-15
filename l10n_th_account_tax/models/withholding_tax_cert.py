# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed.")
    num2words = None

from .account_tax import INCOME_TAX_FORM, WHT_CERT_INCOME_TYPE

TAX_PAYER = [
    ("withholding", "Withholding"),
    ("paid_one_time", "Paid One Time"),
    ("paid_continue", "Paid Continuously"),
]

# Tax payer per standard withholding condition of the payment
L10N_TH_WTH_CONDITION_TAX_PAYER = {
    "at_source": "withholding",
    "forever": "paid_continue",
    "one_time": "paid_one_time",
}

# Types of income per row of the standard 50 Tawi report
TAWI_ROW_INCOME_TYPES = [
    ["1"],
    ["2"],
    ["3"],
    ["4A"],
    False,  # 4(b) dividends
    False,  # (1) with tax credit
    ["4B11"],
    ["4B12"],
    ["4B13"],
    ["4B14"],
    False,  # (2) without tax credit
    ["4B21"],
    ["4B22"],
    ["4B23"],
    ["4B24"],
    ["4B25"],
    ["5"],
    ["6"],
]
# Types of income to specify on the 50 Tawi report
TAWI_OTHER_INCOME_TYPES = ("4B14", "4B25", "6")


class WithholdingTaxCert(models.Model):
    _name = "withholding.tax.cert"
    _inherit = ["mail.thread", "mail.activity.mixin"]  # noqa: RUF012
    _description = "Withholding Tax Certificate"
    _check_company_auto = True

    name = fields.Char(
        string="Number",
        compute="_compute_wht_cert_data",
        store=True,
        tracking=True,
    )
    number = fields.Char(
        string="WHT Number",
        required=True,
        default="/",
        readonly=True,
        copy=False,
    )
    date = fields.Date(
        required=True,
        compute="_compute_wht_cert_data",
        store=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("cancel", "Cancelled")],
        string="Status",
        default="draft",
        copy=False,
        tracking=True,
    )
    ref_wht_cert_id = fields.Many2one(
        string="Ref WHT Cert.",
        comodel_name="withholding.tax.cert",
        tracking=True,
        check_company=True,
        help="This field related from Old WHT Cert.",
    )
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        copy=False,
        domain="[('partner_id', '=', partner_id)]",
        check_company=True,
        ondelete="restrict",
        tracking=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        copy=False,
        domain="[('journal_id.type', '=', 'general'), ('state', '=', 'posted')]",
        check_company=True,
        ondelete="restrict",
        tracking=True,
    )
    company_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Company",
        copy=False,
        default=lambda self: self.env.company.partner_id,
        ondelete="restrict",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor",
        required=True,
        tracking=True,
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Main Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        store=True,
        string="Currency",
    )
    company_vat = fields.Char(related="company_partner_id.vat", string="Company Tax ID")
    partner_vat = fields.Char(related="partner_id.vat", string="Vendor Tax ID")
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM,
        copy=False,
        tracking=True,
    )
    wht_line = fields.One2many(
        comodel_name="withholding.tax.cert.line",
        inverse_name="cert_id",
        string="Withholding Line",
        copy=False,
    )
    tax_payer = fields.Selection(
        selection=TAX_PAYER,
        default="withholding",
        required=True,
        copy=False,
        tracking=True,
    )
    verify_by = fields.Many2one(
        comodel_name="res.users",
        copy=False,
        tracking=True,
    )

    @api.depends("payment_id", "move_id")
    def _compute_wht_cert_data(self):
        for rec in self:
            rec.name = rec.payment_id.name or rec.move_id.name or ""
            rec.date = rec.payment_id.date or rec.move_id.date or rec.date

    @api.model
    def _get_wht_certs_action(self, domain):
        """Withholding tax certificates matching domain, without creation"""
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_th_account_tax.action_withholding_tax_cert_menu"
        )
        action["domain"] = domain
        action["context"] = {"create": False}
        return action

    def action_draft(self):
        return self.write(
            {
                "verify_by": False,
                "state": "draft",
            }
        )

    def action_done(self):
        if any(not line.wht_cert_income_type for line in self.wht_line):
            raise UserError(
                self.env._(
                    "Please select Type of Income on every withholding tax certificate "
                    "line."
                )
            )
        sequence_model = self.env["ir.sequence"]
        for rec in self:
            # Update sequence WHT
            if rec.number == "/":
                rec.number = sequence_model.next_by_code("withholding.tax.cert") or "/"

            if rec.ref_wht_cert_id:
                rec.ref_wht_cert_id.write({"state": "cancel"})
                rec.ref_wht_cert_id.message_post(
                    body=self.env._("This document was substituted by %s.", rec.name)
                )
        self.write({"verify_by": self.env.user.id, "state": "done"})
        return True

    def action_cancel(self):
        self.write(
            {
                "verify_by": False,
                "state": "cancel",
            }
        )
        return True

    @api.constrains("company_id")
    def _check_thai_company(self):
        if any(cert.company_id.account_fiscal_country_id.code != "TH" for cert in self):
            raise ValidationError(
                self.env._("Withholding tax certificates are for Thai companies only.")
            )

    @api.onchange("income_tax_form")
    def _onchange_income_tax_form(self):
        self.wht_line.wht_cert_income_code = False

    def action_print_50_tawi(self):
        """Triggered by the 'Print 50 Tawi' button, as on standard payments"""
        return self.env.ref("l10n_th_account_tax.action_report_wht_cert").report_action(
            self, config=False
        )

    def action_send_by_email(self):
        """Send the 50 Tawi of a done certificate by email"""
        self.ensure_one()
        if self.state != "done":
            raise UserError(
                self.env._("Only a done withholding tax certificate can be sent.")
            )
        template = self.env.ref("l10n_th_account_tax.mail_template_wht_cert")
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_model": self._name,
                "default_res_ids": self.ids,
                "default_template_id": template.id,
                "default_composition_mode": "comment",
                "mail_post_autofollow": True,
            },
        }

    def action_download_50_tawi_bulk(self):
        """Triggered by the 'Thailand: Print 50 tawi' bulk action, as on standard
        payments. Downloads a ZIP of the 50 Tawi of the done certificates."""
        invalid_certs = self.filtered(lambda cert: cert.state != "done")
        valid_certs = self - invalid_certs
        if not valid_certs:
            raise UserError(
                self.env._("No done withholding tax certificate to print 50 Tawi.")
            )
        report = self.env.ref("l10n_th_account_tax.action_report_wht_cert")
        attachments = self.env["ir.attachment"]
        for cert in valid_certs:
            pdf_content, _report_type = report.sudo()._render_qweb_pdf(
                report.report_name, res_ids=cert.ids
            )
            attachments += self.env["ir.attachment"].create(
                {
                    "name": "WHT_{}.pdf".format(cert.number.replace("/", "-")),
                    "type": "binary",
                    "raw": pdf_content,
                    "res_model": cert._name,
                    "res_id": cert.id,
                    "mimetype": "application/pdf",
                }
            )
        download_action = {
            "type": "ir.actions.act_url",
            "url": "/l10n_th_account_tax/download_tawi_reports/{}".format(
                ",".join(map(str, attachments.ids))
            ),
        }
        if invalid_certs:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": self.env._("Notification"),
                    "message": self.env._(
                        "Certificates not done skipped: %s. The done ones are printed.",
                        ", ".join(invalid_certs.mapped("display_name")),
                    ),
                    "type": "warning",
                    "sticky": True,
                    "next": download_action,
                },
            }
        return download_action

    def _get_tawi_income_rows(self, income_rows):
        """Rows of the standard 50 Tawi report, by type of income of the
        certificate lines, one line per row"""
        if len(income_rows) != len(TAWI_ROW_INCOME_TYPES):
            raise UserError(
                self.env._(
                    "The rows of the 50 Tawi report do not match the types of income."
                )
            )
        rows = [
            dict(row, type=income_types, **{"40_8_col": False})
            for row, income_types in zip(
                income_rows, TAWI_ROW_INCOME_TYPES, strict=True
            )
        ]
        # Other incomes (6) on a dotted line, as the signature
        rows[-1].update(label=rows[-1]["label"].rstrip(": "), others_dots=True)
        return rows

    def _get_tawi_amount_text(self, amount):
        """Amount in Thai words, e.g. สามบาทสิบสองสตางค์, สามร้อยบาทถ้วน.
        Standard amount_to_text separates the words, e.g. สาม บาท และ สิบสอง สตางค์"""
        self.ensure_one()
        currency = self.env.ref("base.THB")
        if num2words is None:
            return currency.with_context(lang="th_TH").amount_to_text(amount)
        return num2words(currency.round(amount), to="currency", lang="th")

    def _get_tawi_other_desc(self, income_types):
        """Description of other types of income on the 50 Tawi report"""
        self.ensure_one()
        descs = [
            line.wht_cert_income_desc
            for line in self.wht_line
            if line.wht_cert_income_type in TAWI_OTHER_INCOME_TYPES
            and line.wht_cert_income_type in (income_types or [])
            and line.wht_cert_income_desc
        ]
        return ", ".join(dict.fromkeys(descs))


class WithholdingTaxCertLine(models.Model):
    _name = "withholding.tax.cert.line"
    _description = "Withholding Tax Cert Lines"
    _check_company_auto = True

    cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert", string="WHT Cert", index=True
    )
    wht_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income"
    )
    wht_cert_income_code = fields.Many2one(
        comodel_name="withholding.tax.code.income",
        string="Income Code",
        index=True,
        help="For Text File income code",
    )
    wht_cert_bank_account = fields.Many2one(
        comodel_name="res.partner.bank",
        compute="_compute_wht_bank_account",
        store=True,
        readonly=False,
        check_company=True,
        string="Bank Account",
        help="PND2 type 4A need bank account",
    )
    wht_cert_income_desc = fields.Char(
        string="Income Description", size=500, required=False
    )
    base = fields.Float(string="Base Amount", readonly=False)
    wht_tax_id = fields.Many2one(
        comodel_name="account.tax",
        domain=[("is_withholding_tax", "=", True), ("type_tax_use", "=", "purchase")],
        string="Tax",
        check_company=True,
        readonly=False,
    )
    wht_percent = fields.Float(
        string="% Tax",
        compute="_compute_wht_percent",
    )
    wht_income_tax_form = fields.Selection(
        related="cert_id.income_tax_form",
        index=True,
    )
    amount = fields.Float(string="Tax Amount", readonly=False)
    company_id = fields.Many2one(
        comodel_name="res.company", related="cert_id.company_id"
    )

    @api.depends("wht_tax_id", "amount", "base")
    def _compute_wht_percent(self):
        for rec in self:
            # PIT is progressive (0% on the tax), show its effective rate
            if rec.wht_tax_id.amount_type == "percent" and not rec.wht_tax_id.is_pit:
                rec.wht_percent = abs(rec.wht_tax_id.amount)
            else:
                rec.wht_percent = rec.base and float_round(
                    (rec.amount / rec.base) * 100,
                    precision_rounding=rec.company_id.currency_id.rounding,
                )

    @api.depends("cert_id", "wht_cert_income_type")
    def _compute_wht_bank_account(self):
        for rec in self:
            rec.wht_cert_bank_account = False
            if rec.cert_id.payment_id:
                rec.wht_cert_bank_account = rec.cert_id.payment_id.partner_bank_id.id

    @api.onchange("wht_cert_income_type")
    def _onchange_wht_cert_income_type(self):
        WHT_CODE_INCOME = self.env["withholding.tax.code.income"]
        self.wht_cert_income_desc = False
        self.wht_cert_income_code = False
        if self.wht_cert_income_type:
            select_dict = dict(WHT_CERT_INCOME_TYPE)
            self.wht_cert_income_desc = select_dict[self.wht_cert_income_type]
            income_code = WHT_CODE_INCOME.search(
                [
                    ("wht_cert_income_type", "=", self.wht_cert_income_type),
                    ("income_tax_form", "=", self.cert_id.income_tax_form),
                    ("is_default", "=", True),
                ]
            )
            self.wht_cert_income_code = income_code or False


class WithholdingTaxCodeIncome(models.Model):
    _name = "withholding.tax.code.income"
    _description = "Withholding Tax Code of Income"

    name = fields.Char(required=True)
    code = fields.Char()
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM,
        required=True,
        index=True,
    )
    wht_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income", required=True
    )
    is_default = fields.Boolean(string="Default")

    @api.constrains("is_default")
    def check_is_default(self):
        for code in self.filtered("is_default"):
            code._check_single_default()

    def _check_single_default(self):
        self.ensure_one()
        field_default_duplicate = self.search(
            [
                ("income_tax_form", "=", self.income_tax_form),
                ("wht_cert_income_type", "=", self.wht_cert_income_type),
                ("is_default", "=", True),
            ]
        )
        if len(field_default_duplicate) > 1:
            dict_wht_income_type = dict(WHT_CERT_INCOME_TYPE)
            dict_income_tax_form = dict(INCOME_TAX_FORM)
            raise UserError(
                self.env._(
                    "You can not default field '%(income)s - %(wht_income_type)s' "
                    "more than 1.",
                    income=dict_income_tax_form[self.income_tax_form],
                    wht_income_type=dict_wht_income_type[self.wht_cert_income_type],
                )
            )
