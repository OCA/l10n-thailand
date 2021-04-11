# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


INCOME_TAX_FORM = [('pnd1', 'PND1'),
                   ('pnd1s', 'PND1s'),
                   ('pnd2', 'PND2'),
                   ('pnd2a', 'PND2a'),
                   ('pnd3', 'PND3'),
                   ('pnd3a', 'PND3a'),
                   ('pnd53', 'PND53')]


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


TAX_PAYER = [('withholding', 'Withholding'),
             ('paid_one_time', 'Paid One Time')]


class WithholdingTaxCert(models.Model):
    _name = 'withholding.tax.cert'
    _description = 'Withholding Tax Certificate'

    name = fields.Char(
        string='Number',
        readonly=True,
        related='payment_id.name',
        store=True,
    )
    date = fields.Date(
        string='Date',
        required=True,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
        string='Status',
        default='draft',
        copy=False,
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Payment',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('partner_id', '=', supplier_partner_id)]",
        ondelete='restrict',
    )
    ref_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        # domain="[('partner_id', '=', supplier_partner_id)]",
        ondelete='restrict',
    )
    company_partner_id = fields.Many2one(
        'res.partner',
        string='Company',
        readonly=True,
        copy=False,
        default=lambda self: self.env.user.company_id.partner_id,
        ondelete='restrict',
    )
    supplier_partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        ondelete='restrict',
    )
    company_taxid = fields.Char(
        related='company_partner_id.vat',
        string='Company Tax ID',
        readonly=True,
    )
    supplier_taxid = fields.Char(
        related='supplier_partner_id.vat',
        string='Supplier Tax ID',
        readonly=True,
    )
    income_tax_form = fields.Selection(
        INCOME_TAX_FORM,
        string='Income Tax Form',
        required=True,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    wt_line = fields.One2many(
        'withholding.tax.cert.line',
        'cert_id',
        string='Withholding Line',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    tax_payer = fields.Selection(
        TAX_PAYER,
        string='Tax Payer',
        default='withholding',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )

    @api.onchange('payment_id')
    def _onchange_payment_id(self):
        """ Prepare withholding cert from Payment """
        wt_account_ids = self._context.get('wt_account_ids', [])
        if self.payment_id:
            self.date = self.payment_id.payment_date
            self.supplier_partner_id = self.payment_id.partner_id
            wt_move_lines = self._get_wt_move_line(
                self.payment_id.move_line_ids, wt_account_ids)
            moves = wt_move_lines.mapped('move_id')
            self.update({'ref_move_id': moves and moves[0].id or False})
        if self.ref_move_id:
            wt_move_lines = self._get_wt_move_line(
                self.ref_move_id.line_ids, wt_account_ids)
            CertLine = self.env['withholding.tax.cert.line']
            for line in wt_move_lines:
                self.wt_line += CertLine.new(self._prepare_wt_line(line))

    @api.model
    def _prepare_wt_line(self, move_line):
        """ Hook point to prepare wt_line """
        vals = {
            'wt_cert_income_type': self._context.get('wt_cert_income_type'),
            'wt_percent': False,
            'base': False,
            'amount': abs(move_line.balance),
            'ref_move_line_id': move_line.id, }
        return vals

    @api.model
    def _get_wt_move_line(self, move_lines, wt_account_ids):
        """ Hook point to get wt_move_lines """
        wt_move_lines = move_lines.\
            filtered(lambda l: l.account_id.id in wt_account_ids)
        return wt_move_lines

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True


class WithholdingTaxCertLine(models.Model):
    _name = 'withholding.tax.cert.line'
    _description = 'Withholding Tax Cert Lines'

    cert_id = fields.Many2one(
        'withholding.tax.cert',
        string='WHT Cert',
        index=True,
    )
    wt_cert_income_type = fields.Selection(
        WHT_CERT_INCOME_TYPE,
        string='Type of Income',
        required=True,
    )
    wt_cert_income_desc = fields.Char(
        string='Income Description',
        size=500,
        required=False,
    )
    base = fields.Float(
        string='Base Amount',
        readonly=False,
    )
    wt_percent = fields.Float(
        string='% Tax',
    )
    amount = fields.Float(
        string='Tax Amount',
        readonly=False,
    )
    ref_move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Ref Journal Item',
        readonly=False,
        help="Reference back to journal item which create wt move",
    )

    @api.multi
    @api.constrains('base', 'wt_percent', 'amount')
    def _check_wt_line(self):
        for rec in self:
            prec = self.env.user.company_id.currency_id.decimal_places
            if rec.wt_percent and \
                    float_compare(rec.amount,
                                  rec.base * rec.wt_percent / 100,
                                  prec) != 0:
                raise ValidationError(_('WT Base/Percent/Tax mismatch!'))

    @api.onchange('wt_cert_income_type')
    def _onchange_wt_cert_income_type(self):
        if self.wt_cert_income_type:
            select_dict = dict(WHT_CERT_INCOME_TYPE)
            self.wt_cert_income_desc = select_dict[self.wt_cert_income_type]
        else:
            self.wt_cert_income_desc = False

    @api.onchange('wt_percent')
    def _onchange_wt_percent(self):
        if self.wt_percent:
            self.base = self.amount * 100 / self.wt_percent
        else:
            self.base = 0.0
