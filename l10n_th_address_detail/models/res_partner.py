# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Thai address details with the prefix added when composing the address
L10N_TH_ADDRESS_PREFIXES = {
    "l10n_th_house_number": "",
    "l10n_th_building": "อาคาร ",
    "l10n_th_room": "ห้อง ",
    "l10n_th_floor": "ชั้น ",
    "l10n_th_village": "หมู่บ้าน ",
    "l10n_th_moo": "หมู่ที่ ",
    "l10n_th_soi": "ซอย ",
    "l10n_th_yaek": "แยก ",
    "l10n_th_road": "ถนน",
}
L10N_TH_ADDRESS_DETAILS = tuple(L10N_TH_ADDRESS_PREFIXES)
L10N_TH_ADDRESS_FIELDS = (*L10N_TH_ADDRESS_DETAILS, "l10n_th_address_structured")
L10N_TH_CITY_FIELDS = ("city_id", "l10n_th_subdistrict_id")
L10N_TH_MANAGED_FIELDS = (*L10N_TH_ADDRESS_FIELDS, *L10N_TH_CITY_FIELDS)
# Written values depending on the current address of each partner
L10N_TH_CITY_DEPENDENT_FIELDS = {*L10N_TH_CITY_FIELDS, "city", "state_id", "country_id"}
L10N_TH_PARTNER_DEPENDENT_FIELDS = {
    *L10N_TH_ADDRESS_FIELDS,
    *L10N_TH_CITY_DEPENDENT_FIELDS,
}
X2MANY_TYPES = ("one2many", "many2many")
# Default layout of Street (first line) and Street 2 (second line), in the
# order of the Revenue Department: house no. first, as in most integrations
# Order of the addresses written in Thailand: house number first, road last
L10N_TH_STREET_FORMAT = (
    "%(l10n_th_house_number)s %(l10n_th_moo)s %(l10n_th_village)s "
    "%(l10n_th_building)s %(l10n_th_floor)s %(l10n_th_room)s\n"
    "%(l10n_th_soi)s %(l10n_th_yaek)s %(l10n_th_road)s"
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_th_house_number = fields.Char(string="House No.")
    l10n_th_building = fields.Char(string="Building")
    l10n_th_room = fields.Char(string="Room No.")
    l10n_th_floor = fields.Char(string="Floor")
    l10n_th_village = fields.Char(
        string="Village", help="Name of the village or housing estate (Moo Ban)"
    )
    l10n_th_moo = fields.Char(
        string="Moo", help="Number of the administrative village (Moo Thi)"
    )
    l10n_th_soi = fields.Char(string="Soi")
    l10n_th_yaek = fields.Char(string="Yaek")
    l10n_th_road = fields.Char(string="Road")
    l10n_th_subdistrict_id = fields.Many2one(
        comodel_name="l10n_th.res.city.subdistrict",
        string="Sub-district",
        index="btree_not_null",
        # Not restrict: the module uninstallation removes the sub-districts
        ondelete="set null",
    )
    l10n_th_address_structured = fields.Boolean(
        string="Structured Thai Address",
        compute="_compute_l10n_th_address_structured",
        store=True,
        readonly=False,
        help="Street and Street 2 are generated from the Thai address details. "
        "Unset when Street or Street 2 is edited directly.",
    )

    @api.depends(*L10N_TH_ADDRESS_DETAILS)
    def _compute_l10n_th_address_structured(self):
        for partner in self:
            partner.l10n_th_address_structured = any(
                partner[fname] for fname in L10N_TH_ADDRESS_DETAILS
            )

    @api.onchange(*L10N_TH_ADDRESS_DETAILS)
    def _onchange_l10n_th_address_details(self):
        if self.l10n_th_address_structured:
            values = {fname: self[fname] for fname in L10N_TH_ADDRESS_DETAILS}
            self.street, self.street2 = self._l10n_th_get_street_lines(values)

    @api.onchange("l10n_th_subdistrict_id")
    def _onchange_l10n_th_subdistrict_id(self):
        if self.l10n_th_subdistrict_id:
            self.city_id = self.l10n_th_subdistrict_id.city_id
        if self.city_id.l10n_th_code:
            self._l10n_th_update_city_values()

    @api.onchange("city_id")
    def _onchange_city_id(self):
        if self.l10n_th_subdistrict_id.city_id != self.city_id:
            self.l10n_th_subdistrict_id = False
        if self.city_id.l10n_th_code:
            self._l10n_th_update_city_values()
        # Clearing a Thai district keeps the address, as when saving
        elif self.city_id or not self._origin.city_id.l10n_th_code:
            return super()._onchange_city_id()

    @api.onchange("city", "state_id", "country_id")
    def _onchange_l10n_th_manual_city(self):
        """A manual city, or another province or country, detaches the
        partner from its Thai district and sub-district, as when saving"""
        city = self.city_id
        if city.l10n_th_code and (
            self.city != self._l10n_th_get_city_name(city, self.l10n_th_subdistrict_id)
            or self.state_id != city.state_id
            or self.country_id != city.country_id
        ):
            self.l10n_th_subdistrict_id = False
            self.city_id = False

    def _l10n_th_update_city_values(self):
        values = self._l10n_th_get_city_values(
            self.city_id, self.l10n_th_subdistrict_id, self.zip
        )
        # The address copied from the parent keeps its zip, as in core
        if (
            self.parent_id.l10n_th_subdistrict_id == self.l10n_th_subdistrict_id
            and self.zip == self.parent_id.zip
        ):
            values.pop("zip", None)
        self.update(values)

    @api.model
    def _l10n_th_get_city_name(self, city, subdistrict):
        """Return the city of the address: sub-district and district with
        their prefix, in Thai whatever the language of the user"""
        bangkok = city.state_id.code == "TH-10"
        names = [("เขต" if bangkok else "อำเภอ") + city._l10n_th_get_name()]
        if subdistrict:
            names.insert(0, ("แขวง" if bangkok else "ตำบล") + subdistrict.name)
        return " ".join(names)

    @api.model
    def _l10n_th_get_city_values(self, city, subdistrict, zip_code=False):
        """Return the address values of a Thai district and sub-district. The
        zip is the main one of the sub-district, unless zip_code is one of its
        postal codes."""
        values = {
            "city": self._l10n_th_get_city_name(city, subdistrict),
            "state_id": city.state_id.id,
            "country_id": city.country_id.id,
        }
        if subdistrict and zip_code not in subdistrict._l10n_th_get_zipcodes():
            values["zip"] = subdistrict.zipcode
        return values

    @api.model
    def _l10n_th_get_address_detail(self, values, fname):
        """Return the detail in values with its prefix, unless the value
        already starts with it (e.g. a soi typed as 'ซอยสุขุมวิท 101')"""
        value = self._fields[fname].convert_to_cache(values.get(fname), self) or ""
        value = " ".join(value.split())
        prefix = L10N_TH_ADDRESS_PREFIXES[fname]
        if value and prefix and not value.startswith(prefix.strip()):
            value = prefix + value
        return value

    @api.model
    def _l10n_th_get_street_lines(self, values):
        """Return Street and Street 2 composed from the Thai address details
        in values, following the Thai Street Format of Thailand. Empty lines
        are skipped: Street always holds the first line."""
        street_format = (
            self.env.ref("base.th").l10n_th_street_format or L10N_TH_STREET_FORMAT
        )
        address = street_format % {
            fname: self._l10n_th_get_address_detail(values, fname)
            for fname in L10N_TH_ADDRESS_DETAILS
        }
        lines = [" ".join(line.split()) for line in address.splitlines()]
        lines = [line for line in lines if line] + [False, False]
        return lines[0], lines[1]

    def _l10n_th_prepare_city_vals(self, vals):
        """Return vals to write on the partner (self, empty on create).

        Selecting a sub-district or a Thai district fills the city, province,
        country and zip (unless given). A manual city, or another province or
        country, detaches the partner from its Thai district and sub-district.
        """
        if not vals.keys() & L10N_TH_CITY_DEPENDENT_FIELDS:
            return vals
        # The website and portal forms send an empty city_id for the countries
        # without city selection, like Thailand: an unchanged city keeps the
        # district
        if (
            "city_id" in vals
            and not vals["city_id"]
            and "l10n_th_subdistrict_id" not in vals
            and self.city_id.l10n_th_code
            and "city" in vals
            and vals["city"] == self.city
        ):
            vals = {key: value for key, value in vals.items() if key != "city_id"}
        Subdistrict = self.env["l10n_th.res.city.subdistrict"]
        if "l10n_th_subdistrict_id" in vals:
            subdistrict = Subdistrict.browse(vals["l10n_th_subdistrict_id"])
        else:
            subdistrict = self.l10n_th_subdistrict_id
        if "city_id" in vals:
            city = self.env["res.city"].browse(vals["city_id"])
        else:
            city = self.city_id
        if "l10n_th_subdistrict_id" in vals and subdistrict:
            if "city_id" in vals and city != subdistrict.city_id:
                raise ValidationError(
                    self.env._(
                        "The sub-district %(subdistrict)s is not in the district "
                        "%(city)s.",
                        subdistrict=subdistrict.name,
                        city=city.name,
                    )
                )
            city = subdistrict.city_id
        elif subdistrict.city_id != city:
            subdistrict = Subdistrict
        if not vals.keys() & set(L10N_TH_CITY_FIELDS):
            if city.l10n_th_code and (
                ("city" in vals and vals["city"] != self.city)
                or ("state_id" in vals and vals["state_id"] != city.state_id.id)
                or ("country_id" in vals and vals["country_id"] != city.country_id.id)
            ):
                return {**vals, "city_id": False, "l10n_th_subdistrict_id": False}
            return vals
        vals = {**vals, "city_id": city.id, "l10n_th_subdistrict_id": subdistrict.id}
        if city.l10n_th_code:
            city_values = self._l10n_th_get_city_values(city, subdistrict, self.zip)
            # A zip given with the sub-district is kept
            if "zip" in vals:
                city_values.pop("zip", None)
            vals.update(city_values)
        return vals

    def _l10n_th_prepare_address_vals(self, vals):
        """Return vals to write on the partner (self, empty on create).

        With Thai address details, Street and Street 2 are generated from
        them, even when given in vals. Street or Street 2 given alone is a
        manual address: the details stop generating the street lines.
        """
        if not vals.keys() & set(L10N_TH_ADDRESS_FIELDS):
            if "street" in vals or "street2" in vals:
                return {**vals, "l10n_th_address_structured": False}
            return vals
        values = {
            fname: vals[fname] if fname in vals else self[fname]
            for fname in L10N_TH_ADDRESS_DETAILS
        }
        has_details = any(values.values())
        if not has_details or not vals.get("l10n_th_address_structured", True):
            return vals
        street, street2 = self._l10n_th_get_street_lines(values)
        # The flag is given explicitly, so that the contacts synchronized
        # with the partner get it even when no detail changes
        return {
            **vals,
            "street": street,
            "street2": street2,
            "l10n_th_address_structured": True,
        }

    @api.model
    def _l10n_th_get_parent_address_values(self, values):
        """Return the Thai address values of the parent missing from values,
        when a contact is created with the address of its parent (e.g. copied
        by an import, or the default values of the parent form) but without
        them: core then sees the same address and keeps the contact
        synchronized, instead of making it an other address."""
        if not values.get("parent_id") or values.get("type", "contact") != "contact":
            return {}
        parent = self.browse(values["parent_id"])
        if not (
            parent.l10n_th_address_structured
            or parent.l10n_th_subdistrict_id
            or parent.city_id.l10n_th_code
        ):
            return {}
        parent_address = parent._get_address_values()
        # Without address, core synchronizes the contact with its parent
        address = {
            fname: value for fname in parent_address if (value := values.get(fname))
        }
        if not address or any(
            value != parent_address[fname] for fname, value in address.items()
        ):
            return {}
        return {
            fname: parent_address[fname]
            for fname in L10N_TH_MANAGED_FIELDS
            if fname not in address
        }

    def _l10n_th_prepare_vals(self, vals):
        return self._l10n_th_prepare_address_vals(self._l10n_th_prepare_city_vals(vals))

    @api.model_create_multi
    def create(self, vals_list):
        # Thai address values given by default values are part of the address
        defaults = self.default_get(["type", *self._address_fields()])
        new_vals_list = []
        for vals in vals_list:
            values = {**defaults, **vals}
            new_vals = {
                **vals,
                **{
                    fname: values[fname]
                    for fname in L10N_TH_MANAGED_FIELDS
                    if values.get(fname)
                },
                **self._l10n_th_get_parent_address_values(values),
            }
            new_vals_list.append(self._l10n_th_prepare_vals(new_vals))
        return super().create(new_vals_list)

    def write(self, vals):
        if not vals.keys() & L10N_TH_PARTNER_DEPENDENT_FIELDS:
            return super().write(self._l10n_th_prepare_vals(vals))
        # The address values depend on the current address of each partner,
        # while x2many commands are written once for all as in a batch write
        x2many_vals = {
            fname: value
            for fname, value in vals.items()
            if fname in self._fields and self._fields[fname].type in X2MANY_TYPES
        }
        address_vals = {
            fname: value for fname, value in vals.items() if fname not in x2many_vals
        }
        partners = self
        if not vals.keys() & set(L10N_TH_MANAGED_FIELDS):
            # A city, province or country only matters for the Thai districts
            partners = self.filtered("city_id.l10n_th_code")
            if self - partners:
                super(ResPartner, self - partners).write(
                    self._l10n_th_prepare_address_vals(address_vals)
                )
        for partner in partners:
            super(ResPartner, partner).write(
                partner._l10n_th_prepare_vals(address_vals)
            )
        if x2many_vals:
            super().write(x2many_vals)
        return True

    @api.model
    def _address_fields(self):
        return [
            *super()._address_fields(),
            *L10N_TH_ADDRESS_FIELDS,
            "l10n_th_subdistrict_id",
        ]

    @api.model
    def _l10n_th_update_street_lines(self):
        """Regenerate the street lines of the structured Thai addresses which
        changed, e.g. with the Thai street format, whatever their company"""
        partners = (
            self.sudo()
            .with_context(active_test=False)
            .search([("l10n_th_address_structured", "=", True)])
        )
        partners = partners.filtered(
            lambda partner: (
                (partner.street, partner.street2)
                != partner._l10n_th_get_street_lines(
                    {fname: partner[fname] for fname in L10N_TH_ADDRESS_DETAILS}
                )
            )
        )
        partners.write({"l10n_th_address_structured": True})
