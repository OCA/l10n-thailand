# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

INCOME_TAX_FORM = [
    ("pnd1", "PND1"),
    ("pnd3", "PND3"),
    ("pnd3a", "PND3a"),
    ("pnd53", "PND53"),
]


WHT_CERT_INCOME_TYPE = [
    ("1", "1. เงินเดือน ค่าจ้าง ฯลฯ 40(1)"),
    ("2", "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)"),
    ("3", "3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3)"),
    ("5", "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส"),
    ("6", "6. ค่าบริการ/ค่าสินค้าภาครัฐ"),
    ("7", "7. ค่าจ้างทำของ ค่ารับเหมา"),
    ("8", "8. ธุรกิจพาณิชย์ เกษตร อื่นๆ"),
]


TAX_PAYER = [("withholding", "Withholding"), ("paid_one_time", "Paid One Time")]


class WithholdingTaxCert(models.Model):
    _name = "withholding.tax.cert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Withholding Tax Certificate"

    name = fields.Char(string="Number")
    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("cancel", "Cancelled")],
        string="Status",
        default="draft",
        copy=False,
        tracking=True,
    )
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain=lambda self: self._get_domain_payment_id(),
        ondelete="restrict",
        tracking=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Move",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain=lambda self: self._get_domain_move_id(),
        ondelete="restrict",
        tracking=True,
    )
    company_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Company",
        readonly=True,
        copy=False,
        default=lambda self: self.env.company.partner_id,
        ondelete="restrict",
    )
    supplier_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Main Company",
        required=True,
        readonly=True,
        default=lambda self: self._default_company_id(),
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        store=True,
        string="Currency",
        readonly=True,
    )
    company_taxid = fields.Char(
        related="company_partner_id.vat", string="Company Tax ID", readonly=True
    )
    supplier_taxid = fields.Char(
        related="supplier_partner_id.vat", string="Supplier Tax ID", readonly=True
    )
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM,
        string="Income Tax Form",
        required=True,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    wt_line = fields.One2many(
        comodel_name="withholding.tax.cert.line",
        inverse_name="cert_id",
        string="Withholding Line",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    tax_payer = fields.Selection(
        selection=TAX_PAYER,
        string="Tax Payer",
        default="withholding",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )

    def _get_domain_payment_id(self):
        domain = (
            "[('partner_id', '=', supplier_partner_id), ('wt_cert_ids', '=', False)]"
        )
        return domain

    def _get_domain_move_id(self):
        domain = [
            ("journal_id.type", "=", "general"),
            ("wt_cert_ids", "=", False),
            ("state", "=", "posted"),
        ]
        return domain

    @api.model
    def _default_company_id(self):
        return self.env.company

    @api.onchange("payment_id")
    def _onchange_payment_move_id(self):
        """ Prepare withholding cert """
        wt_account_ids = self._context.get("wt_account_ids", [])
        # Hook to find wt move lines
        wt_move_lines = self._get_wt_move_line(
            self.payment_id, self.move_id, wt_account_ids
        )
        partner_id = self.payment_id.partner_id or self.move_id.partner_id
        # Create Direct Journal Entry and Same Partner in line.
        if self.move_id and self.move_id.type == "entry":
            partner = wt_move_lines.mapped("partner_id")
            if len(partner) == 1:
                partner_id = wt_move_lines[0].partner_id
        self.write(
            {
                "name": self.payment_id.name or self.move_id.name,
                "date": self.payment_id.payment_date or self.move_id.date,
                "supplier_partner_id": partner_id,
            }
        )
        CertLine = self.env["withholding.tax.cert.line"]
        for line in wt_move_lines:
            self.wt_line += CertLine.new(self._prepare_wt_line(line))

    @api.model
    def _prepare_wt_line(self, move_line):
        """ Hook point to prepare wt_line """
        vals = {
            "wt_cert_income_type": self._context.get("wt_cert_income_type"),
            "wt_percent": False,
            "base": False,
            "amount": abs(move_line.balance),
            "ref_move_line_id": move_line.id,
        }
        return vals

    @api.model
    def _get_wt_move_line(self, payment, move, wt_account_ids):
        """ Hook point to get wt_move_lines """
        wt_move_lines = []
        if payment:
            wt_move_lines = payment.move_line_ids.filtered(
                lambda l: l.account_id.id in wt_account_ids
            )
        elif move:
            wt_move_lines = move.line_ids.filtered(
                lambda l: l.account_id.id in wt_account_ids
            )
        return wt_move_lines

    def action_draft(self):
        self.write({"state": "draft"})
        return True

    def action_done(self):
        self.write({"state": "done"})
        return True

    def action_cancel(self):
        self.write({"state": "cancel"})
        return True


class WithholdingTaxCertLine(models.Model):
    _name = "withholding.tax.cert.line"
    _description = "Withholding Tax Cert Lines"

    cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert", string="WHT Cert", index=True
    )
    wt_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income", required=True
    )
    wt_cert_income_desc = fields.Char(
        string="Income Description", size=500, required=False
    )
    base = fields.Float(string="Base Amount", readonly=False)
    wt_percent = fields.Float(string="% Tax")
    amount = fields.Float(string="Tax Amount", readonly=False)
    ref_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Ref Journal Item",
        readonly=False,
        help="Reference back to journal item which create wt move",
    )

    @api.constrains("base", "wt_percent", "amount")
    def _check_wt_line(self):
        for rec in self:
            prec = self.env.company.currency_id.decimal_places
            if (
                rec.wt_percent
                and float_compare(rec.amount, rec.base * rec.wt_percent / 100, prec)
                != 0
            ):
                raise ValidationError(_("WT Base/Percent/Tax mismatch!"))

    @api.onchange("wt_cert_income_type")
    def _onchange_wt_cert_income_type(self):
        if self.wt_cert_income_type:
            select_dict = dict(WHT_CERT_INCOME_TYPE)
            self.wt_cert_income_desc = select_dict[self.wt_cert_income_type]
        else:
            self.wt_cert_income_desc = False

    @api.onchange("wt_percent")
    def _onchange_wt_percent(self):
        if self.wt_percent:
            self.base = self.amount * 100 / self.wt_percent
        else:
            self.base = 0.0
