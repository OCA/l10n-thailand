# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_register_payment(self):
        res = super().action_register_payment()
        ctx = res.get("context", {})
        moves = self.env["account.move"]
        if ctx.get("active_model") == "account.move":
            moves = self.env["account.move"].browse(ctx.get("active_ids", []))
        elif ctx.get("active_model") == "account.move.line":
            lines = self.env["account.move.line"].browse(ctx.get("active_ids", []))
            moves = lines.mapped("move_id")
        # Check move types with invoice settings, whether to use perm
        if moves:
            move_types = set(moves.mapped("move_type"))
            if (
                move_types <= {"out_invoice", "out_refund"}
                and self.env.company.module_payment_register_perm_inbound
            ) or (
                move_types <= {"in_invoice", "in_refund"}
                and self.env.company.module_payment_register_perm_outbound
            ):
                res["name"] = _("Register Payment Form")
                res["res_model"] = "account.payment.register.perm"
                res["target"] = "current"
        return res
