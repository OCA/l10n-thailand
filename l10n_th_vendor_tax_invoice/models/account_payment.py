# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def _create_payment_entry(self, amount):
        if self.payment_type == 'inbound':
            self.taxinv_ready = True
        elif self.payment_type == 'outbound' and self.invoice_ids:
            invoice_lines = self.invoice_ids.mapped('invoice_line_ids')
            taxes = invoice_lines.mapped('invoice_line_tax_ids')
            if not taxes.filtered(lambda l: l.tax_exigibility == 'on_payment'):
                self.taxinv_ready = True
        res = super()._create_payment_entry(amount)
        return res

    @api.multi
    def post(self):
        for payment in self:
            if payment.taxinv_ready:
                payment._check_tax_invoice_manual()
        res = super().post()
        # self._update_tax_invoice_move()
        return res

    @api.multi
    def clear_tax_cash_basis(self):
        for payment in self:
            # Validation
            if not payment.pending_tax_cash_basis_entry:
                raise UserError(_('Tax cash basis is no longer pending'))
            if not payment.taxinv_ready:
                raise UserError(_('Please key-in tax invoice number/date'))
            payment._check_tax_invoice_manual()
            payment._update_tax_invoice_move()
            payment.pending_tax_cash_basis_entry = False
        return True


class AccuntAbstractPayment(models.AbstractModel):
    _inherit = 'account.abstract.payment'

    pending_tax_cash_basis_entry = fields.Boolean(
        default=False,
        help="If pending, payment will has button to clear tax cash basis",
    )
    taxinv_ready = fields.Boolean(
        string="Tax Invoice Ready",
        default=False,
        copy=False,
        help="Tax invoice number is ready for filling in,\n"
        "system will open tax table allow user to fill in",
    )
    tax_line_ids = fields.One2many(
        comodel_name='account.payment.tax',
        inverse_name='payment_id',
        copy=False,
    )

    @api.multi
    def _update_tax_invoice_move(self):
        for payment in self:
            for p in payment.tax_line_ids:
                move_lines = self.env['account.move.line'].search([
                    ('payment_tax_line_id', '=', p.id),
                    ('tax_line_id', '!=', False)])
                # Update new tax invoice info
                for m in move_lines:
                    vals = {'tax_invoice_manual': p.tax_invoice_manual,
                            'tax_date_manual': p.tax_date_manual}
                    m.write(vals)
                # Find move for this payment tax to clear, post it
                move_lines.mapped('move_id').\
                    filtered(lambda m: m.state == 'draft').post()

    @api.multi
    def _check_tax_invoice_manual(self):
        for payment in self:
            no_taxinv_lines = payment.tax_line_ids.\
                filtered(lambda l:
                         not l.tax_invoice_manual or
                         not l.tax_date_manual)
            if no_taxinv_lines:
                raise UserError(_('Tax invoice/date is not filled!'))

    @api.constrains('taxinv_ready', 'pending_tax_cash_basis_entry')
    def _check_tax_invoice(self):
        for payment in self:
            if not payment.taxinv_ready or \
                    not payment.pending_tax_cash_basis_entry:
                continue
            payment._check_tax_invoice_manual()


class AccountPaymentTax(models.Model):
    _name = 'account.payment.tax'
    _description = 'Place to keep tax invoice on payment'

    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Payment',
        index=True,
        readonly=True,
    )
    invoice_tax_line_id = fields.Many2one(
        comodel_name='account.invoice.tax',
        string='Invoice Tax Line',
    )
    name = fields.Char(
        string='Tax Description',
    )
    tax_invoice_manual = fields.Char(
        string='Tax Invoice',
        help="Vendor provided tax invoice number",
    )
    tax_date_manual = fields.Date(
        string='Tax Date',
        help="Vendor provided tax invoice date",
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Company Currency',
        default=lambda self: self.env.user.company_id.currency_id,
    )
    move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Journal Item',
        compute='_compute_move_line_id',
        help="Journal Item that refer to this tax amount",
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        related='move_line_id.move_id',
        readonly=True,
    )
    amount_tax = fields.Monetary(
        currency_field='company_currency_id',
        string='Tax Amount',
        related='move_line_id.balance',
        readonly=True,
    )

    @api.multi
    def _compute_move_line_id(self):
        MoveLine = self.env['account.move.line']
        for rec in self:
            move_line = MoveLine.search([('payment_tax_line_id', '=', rec.id),
                                         ('tax_line_id', '!=', False)])
            rec.move_line_id = move_line
