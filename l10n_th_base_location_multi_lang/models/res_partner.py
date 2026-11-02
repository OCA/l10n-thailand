# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    subdistrict_en = fields.Char(
        string="Sub-District (EN)",
        compute="_compute_address_en",
        store=True,
        readonly=False,
    )
    district_en = fields.Char(
        string="District (EN)",
        compute="_compute_address_en",
        store=True,
        readonly=False,
    )
    state_en = fields.Char(
        string="State (EN)",
        compute="_compute_address_en",
        store=True,
        readonly=False,
    )

    @api.model
    def _address_fields(self):
        return super()._address_fields() + ["subdistrict_en", "district_en", "state_en"]

    @api.depends(
        "zip_id",
        "zip_id.subdistrict_en",
        "zip_id.district_en",
        "zip_id.state_en",
    )
    def _compute_address_en(self):
        for rec in self:
            if rec.zip_id:
                rec.subdistrict_en = rec.zip_id.subdistrict_en
                rec.district_en = rec.zip_id.district_en
                rec.state_en = rec.zip_id.state_en
