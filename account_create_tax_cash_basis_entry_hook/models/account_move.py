# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, api


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    @api.model
    def _set_additional_context(self, move_line):
        ctx = {}
        return self.with_context(ctx)
