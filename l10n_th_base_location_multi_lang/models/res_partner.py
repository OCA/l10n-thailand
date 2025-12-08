# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    subdistrict2_id = fields.Many2one(
        comodel_name="res.subdistrict",
        compute="_compute_subdistrict2_id",
        store=True,
        readonly=False,
        index=True,
        string="Sub-District2 ID",
    )
    city2_id = fields.Many2one(
        comodel_name="res.city",
        compute="_compute_city2_id",
        store=True,
        readonly=False,
        index=True,
        string="City2 ID",
    )
    state2_id = fields.Many2one(
        comodel_name="res.country.state",
        compute="_compute_state2_id",
        store=True,
        readonly=False,
        index=True,
        string="State2 ID",
    )

    @api.model
    def _address_fields(self):
        return super()._address_fields() + ["subdistrict2_id", "city2_id", "state2_id"]

    @api.depends("zip_id")
    def _compute_subdistrict2_id(self):
        subdistrict_model = self.env["res.subdistrict"]
        for rec in self:
            if rec.zip_id:
                subdistrict = rec.zip_id.subdistrict_id
                subdistrict2 = subdistrict_model.search(
                    [("code", "=", subdistrict.code), ("id", "!=", subdistrict.id)],
                    limit=1,
                )
                rec.subdistrict2_id = subdistrict2
            elif not rec.country_enforce_subdistrict:
                rec.subdistrict_id = False

    @api.depends("zip_id")
    def _compute_city2_id(self):
        city_model = self.env["res.city"]
        for rec in self:
            if rec.zip_id:
                city = rec.zip_id.city_id
                city2 = city_model.search(
                    [("code", "=", city.code), ("id", "!=", city.id)], limit=1
                )
                rec.city2_id = city2

    @api.depends("zip_id")
    def _compute_state2_id(self):
        state_model = self.env["res.country.state"]
        for rec in self:
            if rec.zip_id:
                state = rec.zip_id.state_id
                prefix, number = state.code.split("-", 1)
                target_prefix = "TH" if prefix == "EN" else "EN"
                target_code = f"{target_prefix}-{number}"
                state2 = state_model.search(
                    [
                        ("code", "=", target_code),
                    ],
                    limit=1,
                )
                rec.state2_id = state2
