# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TaxAdjustments(models.TransientModel):
    _inherit = 'tax.adjustments.wizard'

    debit_partner_id = fields.Many2one(
        string='Partner (Debit Account)',
        comodel_name='res.partner',
    )
    credit_partner_id = fields.Many2one(
        string='Partner (Credit Account)',
        comodel_name='res.partner',
    )
    tax_date = fields.Date()
    tax_invoice = fields.Char(
        string='Tax Invoice Number',
    )
    amount_tax_base = fields.Monetary(
        string='Tax Base',
        currency_field='company_currency_id',
        required=True,
    )

    @api.one
    @api.constrains('amount', 'amount_tax_base')
    def _check_amount(self):
        if not self.amount or not self.amount_tax_base:
            raise ValidationError(_(
                'Tax Amount or Tax Base can\'t have a zero amount.'))

    @api.multi
    def _create_move(self):
        move_id = super()._create_move()
        move_line = self.env['account.move.line'].search(
            [('move_id', '=', move_id)])
        for line in move_line:
            if line.debit:
                line.partner_id = self.debit_partner_id
            else:
                line.partner_id = self.credit_partner_id
            line.tax_invoice_manual = self.tax_invoice
            line.tax_date_manual = self.tax_date
            line.tax_base_amount = self.amount_tax_base
        return move_id
