# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    subdistrict = fields.Char(
        compute="_compute_subdistrict",
        store=True,
        readonly=False,
    )
    subdistrict_id = fields.Many2one(
        comodel_name="res.subdistrict",
        compute="_compute_subdistrict_id",
        store=True,
        readonly=False,
        index=True,
        string="Sub-District ID",
    )
    country_enforce_subdistrict = fields.Boolean(
        related="country_id.enforce_subdistrict"
    )

    @api.model
    def _address_fields(self):
        return super()._address_fields() + ["subdistrict_id", "subdistrict"]

    @api.depends("subdistrict_id")
    def _compute_subdistrict(self):
        for rec in self:
            rec.subdistrict = rec.subdistrict_id.name

    @api.depends("zip_id")
    def _compute_subdistrict_id(self):
        for rec in self:
            if rec.zip_id:
                rec.subdistrict_id = rec.zip_id.subdistrict_id
            elif not rec.country_enforce_subdistrict:
                rec.subdistrict_id = False
