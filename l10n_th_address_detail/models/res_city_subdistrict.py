# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class L10nThResCitySubdistrict(models.Model):
    _name = "l10n_th.res.city.subdistrict"
    _description = "Thai Sub-district"
    _order = "code"
    _rec_names_search = ("name", "name_en", "code", "zipcode")

    name = fields.Char(required=True, help="Thai name, without prefix")
    name_en = fields.Char(string="English Name")
    code = fields.Char(
        required=True,
        help="Code of the sub-district (khwaeng or tambon) given by the Department "
        "of Provincial Administration (DOPA)",
    )
    city_id = fields.Many2one(
        comodel_name="res.city",
        string="District",
        required=True,
        index=True,
        ondelete="restrict",
    )
    state_id = fields.Many2one(related="city_id.state_id", string="Province")
    zipcode = fields.Char(string="Zip", help="Main postal code of the sub-district")
    zipcodes = fields.Char(
        string="Postal Codes",
        help="All the postal codes of the sub-district, separated by spaces. "
        "Some areas of a sub-district may use another code than the main one.",
    )
    active = fields.Boolean(default=True)

    _code_uniq = models.Constraint(
        "unique(code)", "The code of the sub-district must be unique!"
    )

    @api.depends_context("formatted_display_name")
    @api.depends("name", "city_id", "state_id")
    def _compute_display_name(self):
        for subdistrict in self:
            name = subdistrict.name
            if self.env.context.get("formatted_display_name") and subdistrict.city_id:
                location = ", ".join(
                    filter(None, [subdistrict.city_id.name, subdistrict.state_id.name])
                )
                name = f"{name} \v--{location}--"
            subdistrict.display_name = name

    def _l10n_th_get_zipcodes(self):
        self.ensure_one()
        return (self.zipcodes or self.zipcode or "").split()
