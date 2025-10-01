# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class Country(models.Model):
    _inherit = "res.country"

    enforce_subdistrict = fields.Boolean(
        help="Check this box to ensure every address created in that "
        "country has a 'Sub-District' chosen in the list of the country's subdistrict.",
    )
