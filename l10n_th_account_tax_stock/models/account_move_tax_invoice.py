# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveTaxInvoice(models.Model):
    _inherit = "account.move.tax.invoice"

    is_stock_split = fields.Boolean(
        string="Stock Split",
        copy=False,
        help="When set, this tax invoice represents a proportional share "
        "from a specific stock picking. Amounts are manually maintained "
        "and will not be recomputed automatically.",
    )

    def _compute_tax_amount(self):
        """Skip auto-recompute for records that were split from stock pickings."""
        non_split = self.filtered(lambda r: not r.is_stock_split)
        return super(AccountMoveTaxInvoice, non_split)._compute_tax_amount()
