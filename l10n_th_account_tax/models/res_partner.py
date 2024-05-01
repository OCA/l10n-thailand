# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    pit_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="partner_id",
        string="Personal Income Tax",
        domain=lambda self: self._get_pit_move_ids_domain(),
    )

    @api.model
    def _get_pit_move_ids_domain(self):
        pit_move_ids = (
            self.sudo()
            .env["account.withholding.move"]
            .search([("is_pit", "=", True), ("payment_state", "!=", "draft")])
            .ids
        )
        return [("id", "in", pit_move_ids)]

    def _get_context_pit_monitoring(self):
        ctx = self.env.context.copy()
        ctx.update({"search_default_group_by_calendar_year": 1})
        return ctx

    def action_view_pit_move_yearly_summary(self):
        ctx = self._get_context_pit_monitoring()
        domain = [("is_pit", "=", True), ("partner_id", "=", self.id)]
        return {
            "name": _("Personal Income Tax Yearly"),
            "res_model": "account.withholding.move",
            "view_mode": "pivot,tree,graph",
            "context": ctx,
            "domain": domain,
            "type": "ir.actions.act_window",
        }

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env.ref("l10n_th_account_tax.action_withholding_tax_cert_menu")
        result = action.sudo().read()[0]
        certs = self.env["withholding.tax.cert"].search([("partner_id", "=", self.id)])
        result["domain"] = [("id", "in", certs.ids)]
        return result
