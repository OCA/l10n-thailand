# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _create_tax_cash_basis_moves(self):
        """Undue purchase VAT entries stay draft until the tax is cleared"""
        return super(
            AccountPartialReconcile, self.with_context(hold_undue_vat=True)
        )._create_tax_cash_basis_moves()
