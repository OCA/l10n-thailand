# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_filing_id = fields.Many2one(
        comodel_name="account.tax.filing",
        copy=False,
    )
    tax_filing_adjust_id = fields.Many2one(
        comodel_name="account.tax.filing",
        copy=False,
    )
    is_tax_filing = fields.Boolean(
        copy=False,
        default=False,
    )

    def write(self, vals):
        """Prevent modification of account move line when tax filing is done."""
        if (
            not self._context.get("skip_tax_filing_check")
            and self.tax_filing_id
            and self.tax_filing_id.state != "draft"
        ) or (self.tax_filing_adjust_id and self.tax_filing_adjust_id.state != "draft"):
            raise UserError(
                _("You cannot modify a journal item that has already tax filing.")
            )
        return super().write(vals)
