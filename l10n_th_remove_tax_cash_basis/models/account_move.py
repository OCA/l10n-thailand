# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def create_tax_cash_basis_entry(self, percentage_before_rec):
        res = super(AccountPartialReconcile, self).create_tax_cash_basis_entry(
            percentage_before_rec)
        move_line = self.env['account.move.line'].search([
            ('move_id.tax_cash_basis_rec_id', '=', self.id)]).filtered(
            lambda l: not l.invoice_tax_line_id)
        move_line.unlink()
        return res
