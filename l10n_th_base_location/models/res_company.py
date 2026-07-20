# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

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
        related="partner_id.country_id.enforce_subdistrict"
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
        for record in self:
            if record.zip_id:
                record.subdistrict_id = record.zip_id.subdistrict_id
            elif not record.country_enforce_subdistrict:
                record.subdistrict_id = False

    @api.onchange("zip_id")
    def _onchange_zip_id(self):
        res = super()._onchange_zip_id()
        if self.zip_id and self.country_id.code == "TH":
            district = self.zip_id.city_id
            subdistrict = self.zip_id.subdistrict_id
            self.update(
                {
                    "subdistrict_id": subdistrict.id,
                    "city_id": district.id,
                }
            )
        return res
