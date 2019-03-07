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
        string='Invoice Tax Line',
        copy=False,
        ondelete='restrict',
    )
    payment_tax_line_id = fields.Many2one(
        comodel_name='account.payment.tax',
        string='Payment Tax Line',
        copy=False,
        ondelete='restrict',
    )
    tax_invoice_manual = fields.Char(
        string='Tax Invoice',
        copy=False,
    )
    tax_invoice = fields.Char(
        string='Tax Invoice',
        compute='_compute_tax_invoice',
        store=True,
    )
    tax_date_manual = fields.Date(
        string='Tax Date',
        copy=False,
    )
    tax_date = fields.Char(
        string='Tax Date',
        compute='_compute_tax_invoice',
        store=True,
    )

    @api.model
    def create(self, vals):
        if self._context.get('cash_basis_entry_move_line', False):
            move_line = self._context['cash_basis_entry_move_line']
            print(move_line)
            invoice_tax_line = move_line.invoice_tax_line_id
            payment_tax_line = self.env['account.payment.tax'].search(
                [('invoice_tax_line_id', '=', invoice_tax_line.id),
                 ('payment_id', '=', self._context.get('payment_id'))])
            vals.update({
                'invoice_tax_line_id': invoice_tax_line.id,
                'tax_invoice_manual': invoice_tax_line.tax_invoice_manual,
                'payment_tax_line_id': payment_tax_line.id,
            })
        res = super().create(vals)
        print(vals)
        print(res)
        return res

    @api.multi
    @api.depends('tax_invoice_manual',
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
            self = self.with_context(payment_id=payment.id)
        res = super(AccountPartialReconcile, self).create(vals)
        return res
