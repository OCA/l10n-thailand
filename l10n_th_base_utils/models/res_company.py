# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    font = fields.Selection(
        selection_add=[
            # THBaijam
            ("THBaijam", "THBaijam"),
            ("THBaijam-Bold", "THBaijam Bold"),
            ("THBaijam-Italic", "THBaijam Italic"),
            ("THBaijam-Bold-Italic", "THBaijam Bold Italic"),
            # THChakraPetch
            ("THChakraPetch", "THChakraPetch"),
            ("THChakraPetch-Bold", "THChakraPetch Bold"),
            ("THChakraPetch-Italic", "THChakraPetch Italic"),
            ("THChakraPetch-Bold-Italic", "THChakraPetch Bold Italic"),
            # THCharmofAU
            ("THCharmofAU", "THCharmofAU"),
            # THCharmonman
            ("THCharmonman", "THCharmonman"),
            ("THCharmonman-Bold", "THCharmonman Bold"),
            # THFahKwang
            ("THFahKwang", "THFahKwang"),
            ("THFahKwang-Bold", "THFahKwang Bold"),
            ("THFahKwang-Italic", "THFahKwang Italic"),
            ("THFahKwang-Bold-Italic", "THFahKwang Bold Italic"),
            # THK2DJuly8
            ("THK2DJuly8", "THK2DJuly8"),
            ("THK2DJuly8-Bold", "THK2DJuly8 Bold"),
            ("THK2DJuly8-Italic", "THK2DJuly8 Italic"),
            ("THK2DJuly8-Bold-Italic", "THK2DJuly8 Bold Italic"),
            # THKodchasal
            ("THKodchasal", "THKodchasal"),
            ("THKodchasal-Bold", "THKodchasal Bold"),
            ("THKodchasal-Italic", "THKodchasal Italic"),
            ("THKodchasal-Bold-Italic", "THKodchasal Bold Italic"),
            # THKoHo
            ("THKoHo", "THKoHo"),
            ("THKoHo-Bold", "THKoHo Bold"),
            ("THKoHo-Italic", "THKoHo Italic"),
            ("THKoHo-Bold-Italic", "THKoHo Bold Italic"),
            # THKrub
            ("THKrub", "THKrub"),
            ("THKrub-Bold", "THKrub Bold"),
            ("THKrub-Italic", "THKrub Italic"),
            ("THKrub-Bold-Italic", "THKrub Bold Italic"),
            # THMaliGrade6
            ("THMaliGrade6", "THMaliGrade6"),
            ("THMaliGrade6-Bold", "THMaliGrade6 Bold"),
            ("THMaliGrade6-Italic", "THMaliGrade6 Italic"),
            ("THMaliGrade6-Bold-Italic", "THMaliGrade6 Bold Italic"),
            # THNiramitAS
            ("THNiramitAS", "THNiramitAS"),
            ("THNiramitAS-Bold", "THNiramitAS Bold"),
            ("THNiramitAS-Italic", "THNiramitAS Italic"),
            ("THNiramitAS-Bold-Italic", "THNiramitAS Bold Italic"),
            # THSarabun
            ("THSarabun", "THSarabun"),
            ("THSarabun-Bold", "THSarabun Bold"),
            ("THSarabun-Italic", "THSarabun Italic"),
            ("THSarabun-Bold-Italic", "THSarabun Bold Italic"),
            # THSarabunNew
            ("THSarabunNew", "THSarabunNew"),
            ("THSarabunNew-Bold", "THSarabunNew Bold"),
            ("THSarabunNew-Italic", "THSarabunNew Italic"),
            ("THSarabunNew-Bold-Italic", "THSarabunNew Bold Italic"),
            # THSrisakdi
            ("THSrisakdi", "THSrisakdi"),
            ("THSrisakdi-Bold", "THSrisakdi Bold"),
        ]
    )
