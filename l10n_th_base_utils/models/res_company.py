# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    font = fields.Selection(
        selection_add=[
            ("THSrisakdi", "THSrisakdi"),
            ("THSarabunNew", "THSarabunNew"),
            ("THSarabun", "THSarabun"),
            ("THNiramitAS", "THNiramitAS"),
            ("THMaliGrade6", "THMaliGrade6"),
            ("THKrub", "THKrub"),
            ("THKoHo", "THKoHo"),
            ("THKodchasal", "THKodchasal"),
            ("THK2DJuly8", "THK2DJuly8"),
            ("THFahkwang", "THFahkwang"),
            ("THCharmonman", "THCharmonman"),
            ("THCharmofAU", "THCharmofAU"),
            ("THChakraPetch", "THChakraPetch"),
            ("THBaijam", "THBaijam"),
            ("AngsanaNew", "AngsanaNew"),
            ("Webdings", "Webdings"),
        ]
    )
