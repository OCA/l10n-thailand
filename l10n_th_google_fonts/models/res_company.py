# Copyright 2022 Amin Cheloh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    font = fields.Selection(
        selection_add=[
            ("IBM Plex Sans Thai Looped", "IBM Plex Sans Thai Looped"),
            ("Kanit", "Kanit"),
            ("Sarabun", "Sarabun"),
        ]
    )
