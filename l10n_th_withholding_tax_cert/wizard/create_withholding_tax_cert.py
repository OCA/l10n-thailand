# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CreateWithholdingTaxCert(models.TransientModel):
    _name = 'create.withholding.tax.cert'

    wt_account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Withholing Tax Accounts',
        help="If accounts are specified, system will auto fill tax amount",
        default=lambda self: self._default_wt_account_ids(),
    )

    @api.model
    def _default_wt_account_ids(self):
        payment_id = self._context.get('active_id')
        payment = self.env['account.payment'].browse(payment_id)
        wt_moves = self.env['withholding.tax.move'].search([
            ('payment_line_id', '=', payment.move_line_ids.ids)])
        if wt_moves:
            taxes = wt_moves.mapped('withholding_tax_id')
            accounts = taxes.mapped('account_receivable_id') + \
                taxes.mapped('account_payable_id')
            return accounts
        return False

    @api.multi
    def create_wt_cert(self):
        self.ensure_one()
        ctx = self._context.copy()
        if len(ctx.get('active_ids', [])) != 1:
            raise ValidationError(_('Please select only 1 journal entry.'))
        ctx.update({'default_payment_id': ctx.get('active_id'),
                    'wt_account_ids': self.wt_account_ids.ids})
        return {
            'name': _("Create Withholding Tax Cert."),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'withholding.tax.cert',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
