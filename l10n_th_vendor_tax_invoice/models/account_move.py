# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        """ Do not post when tax_invoice_manual is not ready """
        # Find move line with uncleared undue tax
        move_lines = self.mapped('line_ids').\
            filtered(lambda l: l.tax_exigible and
                     l.tax_line_id.type_tax_use == 'purchase' and
                     l.tax_line_id.tax_exigibility == 'on_payment')
        if move_lines.filtered(lambda l: not l.tax_invoice_manual):
            return False
        return super().post(invoice=invoice)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_tax_line_id = fields.Many2one(
        comodel_name='account.invoice.tax',
        copy=True,
        ondelete='restrict',
    )
    payment_tax_line_id = fields.Many2one(
        comodel_name='account.payment.tax',
        copy=True,
        ondelete='restrict',
    )
    tax_invoice_manual = fields.Char(
        string='Tax Invoice Number',
        copy=True,
    )
    tax_invoice = fields.Char(
        compute='_compute_tax_invoice',
        store=True,
    )
    tax_date_manual = fields.Date(
        copy=True,
    )
    tax_date = fields.Char(
        compute='_compute_tax_invoice',
        store=True,
    )

    @api.model
    def create(self, vals):
        """ Create payment tax line for clear undue vat """
        if self._context.get('cash_basis_entry_move_line', False):
            move_line = self._context['cash_basis_entry_move_line']
            payment = self._context.get('payment')
            invoice_tax_line = move_line.invoice_tax_line_id
            payment_tax_line_id = False
            if move_line.tax_line_id.tax_exigibility == 'on_payment' and \
                    move_line.tax_line_id.type_tax_use == 'purchase':
                payment_tax = self.env['account.payment.tax'].\
                    search([('invoice_tax_line_id', '=', invoice_tax_line.id),
                            ('payment_id', '=', payment.id)])
                if not payment_tax:  # If not already created for this payment
                    currency = self.env.user.company_id.currency_id
                    payment_tax = self.env['account.payment.tax'].create({
                        'invoice_tax_line_id': invoice_tax_line.id,
                        'name': invoice_tax_line.name,
                        'company_currency_id': currency.id,
                        'payment_id': payment.id,
                    })
                payment_tax_line_id = payment_tax.id
            vals.update({
                'invoice_tax_line_id': invoice_tax_line.id,
                'tax_invoice_manual': invoice_tax_line.tax_invoice_manual,
                'payment_tax_line_id': payment_tax_line_id,
            })
        res = super().create(vals)
        return res

    @api.multi
    @api.depends('tax_invoice_manual',
                 'tax_date_manual',
                 'invoice_tax_line_id',
                 'invoice_id.number',
                 'invoice_id.date_invoice')
    def _compute_tax_invoice(self):
        for ml in self.filtered('tax_line_id'):
            # For undue tax on supplier invoice
            if ml.tax_line_id.tax_exigibility == 'on_payment' and \
                    ml.tax_line_id.type_tax_use == 'purchase' and \
                    ml.invoice_id:
                ml.tax_invoice = False
                ml.tax_date = False
            else:  # other cases
                ml.tax_invoice = ml.tax_invoice_manual or \
                    ml.invoice_tax_line_id.tax_invoice or \
                    ml.invoice_id.number
                ml.tax_date = ml.tax_date_manual or \
                    ml.invoice_tax_line_id.tax_date or \
                    ml.invoice_id.date_invoice
        return True


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model
    def create(self, vals):
        """ Check payment, if taxinv_ready is not checked,
            do not create tax cash basis entry invl_id"""
        aml = []
        if vals.get('debit_move_id', False):
            aml.append(vals['debit_move_id'])
        if vals.get('credit_move_id', False):
            aml.append(vals['credit_move_id'])
        # Get value of matched percentage from both move before reconciliating
        lines = self.env['account.move.line'].browse(aml)
        payment = lines.mapped('payment_id')
        if payment and len(payment) == 1 and not payment.taxinv_ready:
            payment.pending_tax_cash_basis_entry = True
        res = super(AccountPartialReconcile, self).create(vals)
        return res

    @api.model
    def _set_additional_context(self, move_line):
        self = super()._set_additional_context(move_line)
        payment = (self.debit_move_id.move_id + self.credit_move_id.move_id).\
            mapped('line_ids').mapped('payment_id')
        ctx = {'cash_basis_entry_move_line': move_line,
               'payment': payment}
        return self.with_context(ctx)
