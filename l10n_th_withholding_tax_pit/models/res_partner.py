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

    def _get_context_pit_monitoring(self):
        ctx = self.env.context.copy()
        ctx.update({"search_default_group_by_calendar_year": 1})
        return ctx

    def action_view_pit_move_yearly_summary(self):
        ctx = self._get_context_pit_monitoring()
        domain = [("partner_id", "=", self.id)]
        return {
            "name": _("Personal Income Tax Yearly"),
            "res_model": "pit.move",
            "view_mode": "pivot,tree,graph",
            "context": ctx,
            "domain": domain,
            "type": "ir.actions.act_window",
        }
