# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models

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
    ("4A", "4. ดอกเบี้ย ฯลฯ 40(4)ก"),
    (
        "4B11",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.1) "
        "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ 30 ของกำไรสุทธิ",
    ),
    (
        "4B12",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.2) "
        "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ 25 ของกำไรสุทธิ",
    ),
    (
        "4B13",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.3) "
        "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ 20 ของกำไรสุทธิ",
    ),
    (
        "4B14",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.4) "
        "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ อื่นๆ (ระบุ) ของกำไรสุทธิ",
    ),
    (
        "4B21",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.1) "
        "กำไรสุทธิกิจการที่ได้รับยกเว้นภาษีเงินได้นิติบุคคล",
    ),
    (
        "4B22",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.2) "
        "ได้รับยกเว้นไม่ต้องนำมารวมคำนวณเป็นรายได้",
    ),
    (
        "4B23",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.3) "
        "กำไรสุทธิส่วนที่หักผลขาดทุนสุทธิยกมาไม่เกิน 5 ปี",
    ),
    (
        "4B24",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.4) "
        "กำไรที่รับรู้ทางบัญชีโดยวิธีส่วนได้เสีย",
    ),
    ("4B25", "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.5) อื่นๆ (ระบุ)"),
    ("5", "5. ค่าจ้างทำของ ค่าบริการ ค่าเช่า ค่าขนส่ง ฯลฯ 3 เตรส"),
    ("6", "6. อื่นๆ (ระบุ)"),
]


TAX_PAYER = [("withholding", "Withholding"), ("paid_one_time", "Paid One Time")]


class WithholdingTaxCert(models.Model):
    _name = "withholding.tax.cert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Withholding Tax Certificate"

    name = fields.Char(
        string="Number",
        compute="_compute_wht_cert_data",
        states={"draft": [("readonly", False)]},
        store=True,
        tracking=True,
    )
    date = fields.Date(
        string="Date",
        required=True,
        compute="_compute_wht_cert_data",
        store=True,
        states={"draft": [("readonly", False)]},
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
        help="This field related from Old WHT Cert.",
    )
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('partner_id', '=', supplier_partner_id)]",
        ondelete="restrict",
        tracking=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Move",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('journal_id.type', '=', 'general')," "('state', '=', 'posted')]",
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
        states={"draft": [("readonly", False)]},
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Main Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
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
        required=False,
        readonly=True,
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    wht_line = fields.One2many(
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

    @api.depends("payment_id", "move_id")
    def _compute_wht_cert_data(self):
        for rec in self:
            rec.name = rec.payment_id.name or rec.move_id.name or ""
            rec.date = rec.payment_id.date or rec.move_id.date

    def action_draft(self):
        self.write({"state": "draft"})
        return True

    def action_done(self):
        for rec in self:
            if rec.ref_wht_cert_id:
                rec.ref_wht_cert_id.write({"state": "cancel"})
                rec.ref_wht_cert_id.message_post(
                    body=_("This document was substituted by %s." % (rec.name))
                )
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
    wht_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income", required=True
    )
    wht_cert_income_desc = fields.Char(
        string="Income Description", size=500, required=False
    )
    base = fields.Float(string="Base Amount", readonly=False)
    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Tax",
        readonly=False,
    )
    wht_percent = fields.Float(
        string="% Tax",
        related="wht_tax_id.amount",
        readonly=True,
    )
    amount = fields.Float(string="Tax Amount", readonly=False)
    company_id = fields.Many2one(
        comodel_name="res.company", related="cert_id.company_id"
    )

    @api.onchange("wht_cert_income_type")
    def _onchange_wht_cert_income_type(self):
        if self.wht_cert_income_type:
            select_dict = dict(WHT_CERT_INCOME_TYPE)
            self.wht_cert_income_desc = select_dict[self.wht_cert_income_type]
        else:
            self.wht_cert_income_desc = False
