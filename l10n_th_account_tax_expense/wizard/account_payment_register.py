# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    bill_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor",
        default=lambda self: self._default_bill_partner_id(),
    )

    def _default_bill_partner_id(self):
        """Try to get default partner used in deduction line
        If cannot get a single partner, user must select it.
        """
        active_ids = self.env.context.get("active_ids", [])
        moves = self.env["account.move"].browse(active_ids)
        expense_partners = moves.mapped("line_ids.expense_id.bill_partner_id")
        partner = expense_partners.id if len(expense_partners) == 1 else False
        if not partner:
            bill_partners = moves.mapped("line_ids.partner_id")
            partner = bill_partners.id if len(bill_partners) == 1 else False
        return partner

    def _prepare_writeoff_move_line(self, write_off_line_vals=None):
        """Update partner for withholding tax"""
        vals = super()._prepare_writeoff_move_line(write_off_line_vals)
        vals[0]["partner_id"] = self.bill_partner_id.id
        return vals
