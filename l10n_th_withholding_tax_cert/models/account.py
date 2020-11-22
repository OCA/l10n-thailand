# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    wt_account = fields.Boolean(
        string='WT Account',
        default=False,
        help="If check, this account is for withholding tax",
    )

    @api.multi
    def button_wt_certs(self):
        return {
            'name': _('Withholding Tax Certs.'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'withholding.tax.cert',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.wt_cert_ids.ids)],
        }
