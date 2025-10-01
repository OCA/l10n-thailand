# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = ["res.partner"]

    subdistrict_id = fields.Many2one(
        comodel_name="res.subdistrict", string="Sub-District ID"
    )
    country_enforce_subdistrict = fields.Boolean(
        related="country_id.enforce_subdistrict"
    )

    @api.model
    def _address_fields(self):
        return super()._address_fields() + ["subdistrict_id"]
