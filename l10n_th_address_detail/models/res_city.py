# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCity(models.Model):
    _inherit = "res.city"
    _rec_names_search = ("name", "zipcode", "l10n_th_code", "l10n_th_name_en")

    l10n_th_code = fields.Char(
        string="Thai District Code",
        index="btree_not_null",
        help="Code of the district (khet or amphoe) given by the Department of "
        "Provincial Administration (DOPA)",
    )
    l10n_th_name_en = fields.Char(string="English Name")
    l10n_th_subdistrict_ids = fields.One2many(
        comodel_name="l10n_th.res.city.subdistrict",
        inverse_name="city_id",
        string="Sub-districts",
    )

    _l10n_th_code_uniq = models.Constraint(
        "unique(l10n_th_code)", "The Thai district code must be unique!"
    )

    def _l10n_th_get_name(self):
        """Thai name of the district: the source value of the name, whatever
        the language of the user"""
        self.ensure_one()
        return self.with_context(lang="en_US").name
