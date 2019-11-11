# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveTaxInvoice(models.Model):
    _name = 'account.move.tax.invoice'
    _description = 'Tax Invoice Info'

    tax_invoice_number = fields.Char(
        string='Tax Invoice Number',
        copy=False,
    )
    tax_invoice_date = fields.Date(
        string='Tax Invoice Date',
        copy=False,
    )
    move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        index=True,
        copy=False,
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        related='move_line_id.move_id',
        store=True,
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        compute='_compute_payment_id',
        store=True,
    )
    to_clear_tax = fields.Boolean(
        related='payment_id.to_clear_tax',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='move_id.company_id',
        store=True,
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        related='move_line_id.account_id',
    )
    tax_line_id = fields.Many2one(
        comodel_name='account.tax',
        related='move_line_id.tax_line_id',
    )
    tax_base_amount = fields.Monetary(
        string='Tax Base',
        currency_field='company_currency_id',
        related='move_line_id.tax_base_amount',
    )
    balance = fields.Monetary(
        string='Tax Amount',
        currency_field='company_currency_id',
        related='move_line_id.balance',
    )

    @api.depends('move_line_id')
    def _compute_payment_id(self):
        self.write({'payment_id': self._context.get('payment_id')})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tax_invoice_id = fields.Many2one(
        comodel_name='account.move.tax.invoice',
        index=True,
        required=False,
        ondelete='restrict',
    )

    def create(self, vals):
        move_lines = super().create(vals)
        TaxInvoice = self.env['account.move.tax.invoice']
        for line in move_lines:
            if line.tax_line_id and line.tax_exigible:
                taxinv = TaxInvoice.create({'move_line_id': line.id})
                line.tax_invoice_id = taxinv
        return move_lines

    def unlink(self):
        tax_invoices = self.mapped('tax_invoice_id')
        res = super().unlink()
        tax_invoices.unlink()
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    tax_invoice_ids = fields.One2many(
        comodel_name='account.move.tax.invoice',
        inverse_name='move_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )

    def post(self):
        """
        Additional tax invoice info (tax_invoice_number, tax_invoice_date)
        Case sales tax, use Odoo's info, as document is issued out.
        Case purchase tax, use vendor's info to fill back.
        """
        # Purchase Taxes
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                    lambda l: l.tax_line_id.type_tax_use == 'purchase'):
                if not tax_invoice.tax_invoice_number or \
                        not tax_invoice.tax_invoice_date:
                    if tax_invoice.payment_id:  # Defer posting for payment
                        tax_invoice.payment_id.write({'to_clear_tax': True})
                        return False
                    else:
                        raise UserError(
                            _('Please fill in tax invoice and tax date'))

        res = super().post()

        # Sales Taxes
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                    lambda l: l.tax_line_id.type_tax_use == 'sale'):
                tax_invoice.write({
                    'tax_invoice_number': move.name,
                    'tax_invoice_date': move.date,
                })
        return res


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def create_tax_cash_basis_entry(self, percentage_before_rec):
        """This method is called from the move lines that
        create cash basis entry. We want to use the same payment_id when
        create account.move.tax.invoice"""
        move_lines = self.debit_move_id | self.credit_move_id
        payment = move_lines.mapped('payment_id')
        payment.ensure_one()
        self = self.with_context(payment_id=payment.id)
        return super().create_tax_cash_basis_entry(percentage_before_rec)
