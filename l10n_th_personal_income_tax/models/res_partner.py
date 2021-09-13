# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    pit_line = fields.One2many(
        comodel_name="pit.move",
        inverse_name="partner_id",
        string="Personal Income Tax",
        domain=[("payment_state", "!=", "draft")],
    )
    pit_yearly = fields.One2many(
        comodel_name="pit.move.yearly",
        inverse_name="partner_id",
        string="PIT Yearly",
        readonly=True,
    )

    def _get_context_pit_monitoring(self):
        ctx = self._context.copy()
        return ctx

    def action_view_pit_yearly_summary(self):
        ctx = self._get_context_pit_monitoring()
        return {
            "name": _("Personal Income Tax Yearly"),
            "res_model": "pit.move.yearly",
            "view_mode": "pivot,tree,graph",
            "context": ctx,
            "type": "ir.actions.act_window",
        }
