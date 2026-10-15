# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    wht_cert_count = fields.Integer(
        string="# Withholding Tax Certs",
        compute="_compute_wht_cert_count",
    )
    show_pit_income = fields.Boolean(compute="_compute_show_pit_income")

    def _compute_wht_cert_count(self):
        counts = dict(
            self.env["withholding.tax.cert"]._read_group(
                [("partner_id", "in", self.ids)],
                groupby=["partner_id"],
                aggregates=["__count"],
            )
        )
        for partner in self:
            partner.wht_cert_count = counts.get(partner, 0)

    @api.depends("commercial_partner_id.is_company")
    @api.depends_context("company")
    def _compute_show_pit_income(self):
        """Personal income tax is for individuals, in Thai companies only"""
        is_thai = self.env.company.account_fiscal_country_id.code == "TH"
        for partner in self:
            partner.show_pit_income = (
                is_thai and not partner.commercial_partner_id.is_company
            )

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_th_account_tax.action_withholding_tax_cert_menu"
        )
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {"create": False}
        return action

    def action_view_pit_income(self):
        """Personal income tax income and withholding of the partner"""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_th_account_tax.action_pit_report"
        )
        action["domain"] = [("partner_id", "=", self.id), ("is_pit", "=", True)]
        action["context"] = {"pivot_row_groupby": ["calendar_year"]}
        return action
