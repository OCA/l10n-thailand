# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountMoveTaxInvoice(models.Model):
    _inherit = "account.move.tax.invoice"

    branch_id = fields.Many2one(
        comodel_name="res.branch",
        string="Branch",
        compute="_compute_branch",
        store=True,
        readonly=False,
    )

    @api.depends("move_id.branch_id")
    def _compute_branch(self):
        for rec in self:
            # Get branch from operating unit move
            if rec.payment_id:
                moves = (
                    rec.payment_id.reconciled_bill_ids
                    or rec.payment_id.reconciled_invoice_ids
                )
                move_branch = moves.mapped("branch_id")
            else:
                move_branch = rec.move_id.branch_id
            rec.branch_id = move_branch.id
