# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    tax_filing_id = fields.Many2one(
        comodel_name="account.tax.filing",
        copy=False,
    )

    def unlink(self):
        if self.tax_filing_id:
            self.tax_filing_id.write(
                {
                    "state": "confirm",
                }
            )
        return super(AccountMove, self).unlink()

    def _get_tax_filing_amls(self):
        """Helper used to retrieve the tax filing move lines on this Journal Entries"""
        self.ensure_one()
        return self.line_ids.filtered(
            lambda line: line.tax_filing_id and line.tax_filing_id.state != "draft"
        )

    def button_draft(self):
        for rec in self:
            if rec._get_tax_filing_amls():
                raise UserError(
                    _("Cannot set to draft entries have already been tax filing")
                )
        return super().button_draft()
