# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    guarantee_ids = fields.Many2many(
        comodel_name="purchase.guarantee",
        relation="account_move_guarantee_rel",
        column1="move_id",
        column2="guarantee_id",
        string="Guarantee",
        ondelete="restrict",
    )
    return_guarantee_ids = fields.Many2many(
        comodel_name="purchase.guarantee",
        relation="account_move_return_guarantee_rel",
        column1="move_id",
        column2="guarantee_id",
        string="Return Guarantee",
        ondelete="restrict",
    )

    def _prepare_guarantee_move_line(self, guarantee):
        self.ensure_one()
        return {
            "name": guarantee.guarantee_method_id.name,
            "account_id": guarantee.guarantee_method_id.account_id.id,
            "quantity": 1,
            "price_unit": guarantee.amount,
            "analytic_account_id": guarantee.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, guarantee.analytic_tag_ids.ids)],
            "move_id": self.id,
        }

    @api.onchange("guarantee_ids")
    def _onchange_guarantee_ids(self):
        for rec in self:
            # Clear invoice lines
            rec.line_ids = False
            # New invoice lines
            new_lines = rec.env["account.move.line"]
            for guarantee in rec.guarantee_ids:
                new_line = new_lines.new(rec._prepare_guarantee_move_line(guarantee))
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()
            rec._onchange_currency()

    @api.onchange("return_guarantee_ids")
    def _onchange_return_guarantee_ids(self):
        for rec in self:
            # Clear invoice lines
            rec.line_ids = False
            # New invoice lines
            new_lines = rec.env["account.move.line"]
            for line in rec.return_guarantee_ids.mapped("invoice_ids.invoice_line_ids"):
                new_line = new_lines.new(
                    {field: line[field] for field in list(line._fields.keys())}
                )
                new_line["move_id"] = rec.id
                new_line._onchange_price_subtotal()
                new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()
            rec._onchange_currency()

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        for rec in self.filtered(lambda l: l.guarantee_ids or l.return_guarantee_ids):
            rec.update(
                {
                    "guarantee_ids": False,
                    "return_guarantee_ids": False,
                    "line_ids": False,
                    "invoice_line_ids": False,
                }
            )
        return res
