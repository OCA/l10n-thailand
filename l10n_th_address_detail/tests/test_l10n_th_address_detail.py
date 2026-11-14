# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.l10n_th_address_detail.hooks import post_init_hook
from odoo.addons.l10n_th_address_detail.models.res_partner import L10N_TH_STREET_FORMAT


class TestL10nThAddressDetail(BaseCommon):
    _test_user_groups = ("base.group_user", "base.group_partner_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_th = cls.env.ref("base.th")
        # As set by the module installation, whatever the database config
        cls.country_th.sudo().write(
            {"enforce_cities": True, "l10n_th_street_format": L10N_TH_STREET_FORMAT}
        )
        cls.subdistrict_palace = cls.env.ref(
            "l10n_th_address_detail.subdistrict_th_100101"
        )
        cls.subdistrict_tha_raeng = cls.env.ref(
            "l10n_th_address_detail.subdistrict_th_100508"
        )
        cls.subdistrict_si_phum = cls.env.ref(
            "l10n_th_address_detail.subdistrict_th_500101"
        )
        cls.city_dusit = cls.env.ref("l10n_th_address_detail.city_th_1002")
        cls.state_bangkok = cls.env.ref("base.state_th_001")
        cls.details = {
            "l10n_th_house_number": "99/1",
            "l10n_th_building": "เอ",
            "l10n_th_room": "1204",
            "l10n_th_floor": "12",
            "l10n_th_village": "สุขสันต์",
            "l10n_th_moo": "5",
            "l10n_th_soi": "สุขุมวิท 101",
            "l10n_th_yaek": "3",
            "l10n_th_road": "สุขุมวิท",
        }
        cls.street = "99/1 หมู่ที่ 5 หมู่บ้าน สุขสันต์ อาคาร เอ ชั้น 12 ห้อง 1204"
        cls.street2 = "ซอย สุขุมวิท 101 แยก 3 ถนนสุขุมวิท"

    def _create_partner(self, **vals):
        return self.env["res.partner"].create(
            {"name": "Thai Partner", "country_id": self.country_th.id, **vals}
        )

    def test_01_structured_address(self):
        """The street lines are generated from the address details"""
        partner = self._create_partner(**self.details)
        self.assertTrue(partner.l10n_th_address_structured)
        self.assertEqual(partner.street, self.street)
        self.assertEqual(partner.street2, self.street2)
        # Details win over street lines given with them (e.g. an import)
        partner = self._create_partner(
            **self.details, street="Old street", street2="Old street 2"
        )
        self.assertEqual(partner.street, self.street)
        self.assertEqual(partner.street2, self.street2)
        # A prefix typed by the user is not doubled
        partner.write({"l10n_th_soi": "ซอยสุขุมวิท 101", "l10n_th_road": "ถนนพระราม 4"})
        self.assertEqual(partner.street2, "ซอยสุขุมวิท 101 แยก 3 ถนนพระราม 4")
        # Updating or clearing a detail regenerates the lines
        partner.write({"l10n_th_building": False, "l10n_th_room": False})
        self.assertEqual(partner.street, "99/1 หมู่ที่ 5 หมู่บ้าน สุขสันต์ ชั้น 12")
        # Street holds the first line when only details of Street 2 are set
        partner.write({fname: False for fname in self.details})
        partner.write({"l10n_th_soi": "5", "l10n_th_road": "สุขุมวิท"})
        self.assertEqual(partner.street, "ซอย 5 ถนนสุขุมวิท")
        self.assertFalse(partner.street2)
        # Values converted like Char fields (e.g. numbers from an integration)
        partner.l10n_th_house_number = 7
        self.assertEqual(partner.street, "7")
        # Details given by default values are part of the address
        partner = (
            self.env["res.partner"]
            .with_context(default_l10n_th_road="สุขุมวิท")
            .create({"name": "Thai Partner", "l10n_th_house_number": "1"})
        )
        self.assertEqual(partner.street, "1")
        self.assertEqual(partner.street2, "ถนนสุขุมวิท")

    def test_02_manual_address(self):
        """Editing the street lines directly stops generating them"""
        partner = self._create_partner(**self.details)
        partner.street = "Manual street"
        self.assertFalse(partner.l10n_th_address_structured)
        self.assertEqual(partner.street, "Manual street")
        self.assertEqual(partner.street2, self.street2)
        self.assertEqual(partner.l10n_th_house_number, "99/1")
        # Other writes keep the manual address
        partner.write({"phone": "021234567", "city": "Bangkok"})
        self.assertEqual(partner.street, "Manual street")
        # Editing a detail makes the details the address again
        partner.l10n_th_house_number = "100"
        self.assertTrue(partner.l10n_th_address_structured)
        self.assertEqual(partner.street, self.street.replace("99/1", "100"))
        # A partner without details keeps its street lines
        partner = self._create_partner(street="1 Main Road", street2="Unit 2")
        self.assertFalse(partner.l10n_th_address_structured)
        partner.write({"street2": "Unit 3", "zip": "10110"})
        self.assertEqual(partner.street, "1 Main Road")
        self.assertEqual(partner.street2, "Unit 3")

    def test_03_multi_partner_write(self):
        """The street lines come from the details of each partner"""
        partner1 = self._create_partner(**self.details)
        # Both street lines are generated, Street 2 has no detail here
        partner2 = self._create_partner(l10n_th_house_number="7", street2="Unit 2")
        self.assertEqual(partner2.street, "7")
        self.assertFalse(partner2.street2)
        # x2many commands are written once, as in a normal batch write
        (partner1 | partner2).write(
            {
                "l10n_th_road": "พหลโยธิน",
                "category_id": [Command.create({"name": "Thai Address Tag"})],
            }
        )
        self.assertEqual(len(partner1.category_id | partner2.category_id), 1)
        self.assertEqual(partner1.street, self.street)
        self.assertEqual(partner1.street2, "ซอย สุขุมวิท 101 แยก 3 ถนนพหลโยธิน")
        self.assertEqual(partner2.street, "7")
        self.assertEqual(partner2.street2, "ถนนพหลโยธิน")

    def test_04_contact_address_sync(self):
        """Contacts share the address details of their company"""
        company = self._create_partner(is_company=True, **self.details)
        contact = self.env["res.partner"].create(
            {"name": "Contact", "parent_id": company.id, "type": "contact"}
        )
        self.assertEqual(contact.l10n_th_house_number, "99/1")
        self.assertTrue(contact.l10n_th_address_structured)
        self.assertEqual(contact.street, self.street)
        self.assertEqual(contact.street2, self.street2)
        # Downstream: from the company to the contact
        company.l10n_th_floor = "15"
        self.assertEqual(contact.l10n_th_floor, "15")
        self.assertEqual(contact.street, self.street.replace("ชั้น 12", "ชั้น 15"))
        # Upstream: from the contact to the company
        contact.l10n_th_soi = "ลาซาล"
        self.assertEqual(company.l10n_th_soi, "ลาซาล")
        self.assertEqual(company.street2, "ซอย ลาซาล แยก 3 ถนนสุขุมวิท")
        # A manual address is synchronized as well
        company.street = "Manual street"
        self.assertEqual(contact.street, "Manual street")
        self.assertFalse(contact.l10n_th_address_structured)
        # Editing a detail again, even unchanged, regenerates both addresses
        company.l10n_th_house_number = "99/1"
        self.assertTrue(contact.l10n_th_address_structured)
        self.assertEqual(contact.street, self.street.replace("ชั้น 12", "ชั้น 15"))
        # A contact created with the address of its company but without the
        # details (e.g. an import, or the defaults of the company form) stays
        # synchronized
        contact2 = self.env["res.partner"].create(
            {
                "name": "Contact 2",
                "parent_id": company.id,
                "street": company.street,
                "street2": company.street2,
                "country_id": self.country_th.id,
            }
        )
        self.assertEqual(contact2.type, "contact")
        self.assertEqual(contact2.l10n_th_soi, "ลาซาล")
        contact3 = (
            self.env["res.partner"]
            .with_context(
                default_street=company.street,
                default_street2=company.street2,
                default_country_id=self.country_th.id,
            )
            .create({"name": "Contact 3", "parent_id": company.id})
        )
        self.assertEqual(contact3.type, "contact")
        self.assertTrue(contact3.l10n_th_address_structured)
        # Another address of the company is independent
        delivery = self.env["res.partner"].create(
            {
                "name": "Delivery",
                "parent_id": company.id,
                "type": "delivery",
                "l10n_th_house_number": "5",
            }
        )
        self.assertEqual(delivery.street, "5")
        self.assertEqual(company.l10n_th_house_number, "99/1")

    def test_05_form(self):
        """The form shows the generated street lines before saving"""
        with Form(self.env["res.partner"]) as partner_form:
            partner_form.name = "Thai Partner"
            partner_form.country_id = self.country_th
            partner_form.street = "Manual street"
            partner_form.l10n_th_house_number = "99/1"
            partner_form.l10n_th_road = "สุขุมวิท"
            self.assertEqual(partner_form.street, "99/1")
            self.assertEqual(partner_form.street2, "ถนนสุขุมวิท")
        partner = partner_form.record
        self.assertTrue(partner.l10n_th_address_structured)
        self.assertEqual(partner.street, "99/1")
        self.assertEqual(partner.street2, "ถนนสุขุมวิท")
        # A manual street typed after the details is kept
        with Form(partner) as partner_form:
            partner_form.street = "Manual street"
        self.assertEqual(partner.street, "Manual street")
        self.assertFalse(partner.l10n_th_address_structured)

    def test_06_street_format(self):
        """The street lines follow the Thai street format of Thailand"""
        country_th = self.country_th.sudo()
        country_th.write({"enforce_cities": False, "l10n_th_street_format": False})
        post_init_hook(self.env(su=True))
        self.assertTrue(country_th.enforce_cities)
        self.assertEqual(country_th.l10n_th_street_format, L10N_TH_STREET_FORMAT)
        partner = self._create_partner(**self.details)
        manual_partner = self._create_partner(**self.details)
        manual_partner.street = "Manual street"
        # All the details in Street: the structured addresses are regenerated
        country_th.l10n_th_street_format = L10N_TH_STREET_FORMAT.replace("\n", " ")
        self.assertEqual(partner.street, f"{self.street} {self.street2}")
        self.assertFalse(partner.street2)
        self.assertEqual(manual_partner.street, "Manual street")
        # Soi in Street, and the details missing from the format are not shown
        country_th.l10n_th_street_format = (
            "%(l10n_th_house_number)s %(l10n_th_soi)s\n%(l10n_th_road)s"
        )
        self.assertEqual(partner.street, "99/1 ซอย สุขุมวิท 101")
        self.assertEqual(partner.street2, "ถนนสุขุมวิท")
        partner.l10n_th_house_number = "100"
        self.assertEqual(partner.street, "100 ซอย สุขุมวิท 101")
        # Without format, the default one applies
        country_th.l10n_th_street_format = False
        self.assertEqual(partner.street, self.street.replace("99/1", "100"))
        self.assertEqual(partner.street2, self.street2)
        # Details all missing from the format leave the street lines empty
        country_th.l10n_th_street_format = "%(l10n_th_road)s"
        house_partner = self._create_partner(l10n_th_house_number="1", street="Old")
        self.assertFalse(house_partner.street)
        country_th.l10n_th_street_format = "%(l10n_th_house_number)s 100%%"
        self.assertEqual(house_partner.street, "1 100%")
        with self.assertRaises(ValidationError):
            country_th.l10n_th_street_format = "%(l10n_th_house_number)s %(name)s"
        with self.assertRaises(ValidationError):
            country_th.l10n_th_street_format = "%s"
        with self.assertRaises(ValidationError):
            country_th.l10n_th_street_format = "%(l10n_th_soi)r"
        with self.assertRaises(ValidationError):
            country_th.l10n_th_street_format = (
                "%(l10n_th_soi)s\n%(l10n_th_moo)s\n%(l10n_th_road)s"
            )

    def test_07_subdistrict_address(self):
        """The sub-district fills the city, province, country and zip"""
        partner = self.env["res.partner"].create(
            {
                "name": "Thai Partner",
                "l10n_th_subdistrict_id": self.subdistrict_palace.id,
                **self.details,
            }
        )
        self.assertEqual(partner.city_id, self.subdistrict_palace.city_id)
        self.assertEqual(partner.city, "แขวงพระบรมมหาราชวัง เขตพระนคร")
        self.assertEqual(partner.state_id, self.state_bangkok)
        self.assertEqual(partner.country_id, self.country_th)
        self.assertEqual(partner.zip, "10200")
        # The street lines still come from the details
        self.assertEqual(partner.street, self.street)
        # Outside Bangkok: tambon and amphoe
        partner.l10n_th_subdistrict_id = self.subdistrict_si_phum
        self.assertEqual(partner.city, "ตำบลศรีภูมิ อำเภอเมืองเชียงใหม่")
        self.assertEqual(partner.state_id.code, "TH-50")
        self.assertEqual(partner.zip, "50200")
        # Another postal code of the sub-district is kept, given or existing
        partner.write(
            {"l10n_th_subdistrict_id": self.subdistrict_tha_raeng.id, "zip": "10230"}
        )
        self.assertEqual(partner.zip, "10230")
        partner.write({"l10n_th_subdistrict_id": False})
        partner.l10n_th_subdistrict_id = self.subdistrict_tha_raeng
        self.assertEqual(partner.zip, "10230")
        partner.write({"zip": "99999"})
        self.assertEqual(partner.l10n_th_subdistrict_id, self.subdistrict_tha_raeng)
        self.assertEqual(partner.zip, "99999")
        partner.l10n_th_subdistrict_id = self.subdistrict_palace
        self.assertEqual(partner.zip, "10200")
        # Another district clears the sub-district
        partner.city_id = self.city_dusit
        self.assertFalse(partner.l10n_th_subdistrict_id)
        self.assertEqual(partner.city, "เขตดุสิต")
        with self.assertRaises(ValidationError):
            partner.write(
                {
                    "l10n_th_subdistrict_id": self.subdistrict_palace.id,
                    "city_id": self.city_dusit.id,
                }
            )
        # The same city keeps the district, a manual city detaches it
        partner.l10n_th_subdistrict_id = self.subdistrict_palace
        partner.write({"city": partner.city, "phone": "021234567"})
        self.assertEqual(partner.l10n_th_subdistrict_id, self.subdistrict_palace)
        partner.city = "Manual city"
        self.assertFalse(partner.city_id)
        self.assertFalse(partner.l10n_th_subdistrict_id)
        self.assertEqual(partner.city, "Manual city")
        self.assertEqual(partner.zip, "10200")
        # Another province detaches it as well
        partner.l10n_th_subdistrict_id = self.subdistrict_palace
        partner.state_id = self.subdistrict_si_phum.state_id
        self.assertFalse(partner.city_id)
        # The website and portal forms send an empty district with the city
        partner.l10n_th_subdistrict_id = self.subdistrict_palace
        partner.write({"city_id": False, "city": partner.city, "phone": "029999999"})
        self.assertEqual(partner.l10n_th_subdistrict_id, self.subdistrict_palace)
        # Clearing the district keeps the address
        partner.city_id = False
        self.assertFalse(partner.l10n_th_subdistrict_id)
        self.assertEqual(partner.city, "แขวงพระบรมมหาราชวัง เขตพระนคร")
        # A removed sub-district leaves the contact without it
        partner.l10n_th_subdistrict_id = self.subdistrict_si_phum
        self.subdistrict_si_phum.sudo().unlink()
        self.assertFalse(partner.l10n_th_subdistrict_id)
        self.assertEqual(partner.city_id.l10n_th_code, "5001")
        # Cities of other countries keep the standard behaviour
        city_us = self.env["res.city"].create(
            {"name": "Springfield", "country_id": self.env.ref("base.us").id}
        )
        partner_us = self.env["res.partner"].create(
            {"name": "US Partner", "city_id": city_us.id, "city": "Springfield"}
        )
        partner_us.city = "Shelbyville"
        self.assertEqual(partner_us.city_id, city_us)
        # Districts and sub-districts are found by code and English name
        Subdistrict = self.env["l10n_th.res.city.subdistrict"]
        self.assertIn(
            self.subdistrict_palace,
            Subdistrict.search([("display_name", "ilike", "100101")]),
        )
        self.assertIn(
            self.city_dusit,
            self.env["res.city"].search([("display_name", "ilike", "Dusit")]),
        )

    def test_08_subdistrict_contact_sync(self):
        """Contacts share the district and sub-district of their company"""
        company = self.env["res.partner"].create(
            {
                "name": "Thai Company",
                "is_company": True,
                "l10n_th_subdistrict_id": self.subdistrict_palace.id,
            }
        )
        contact = self.env["res.partner"].create(
            {"name": "Contact", "parent_id": company.id}
        )
        self.assertEqual(contact.l10n_th_subdistrict_id, self.subdistrict_palace)
        self.assertEqual(contact.city, company.city)
        company.l10n_th_subdistrict_id = self.subdistrict_tha_raeng
        self.assertEqual(contact.l10n_th_subdistrict_id, self.subdistrict_tha_raeng)
        self.assertEqual(contact.city, "แขวงท่าแร้ง เขตบางเขน")
        self.assertEqual(contact.zip, "10220")
        # Created with the address of its company, without sub-district
        contact2 = self.env["res.partner"].create(
            {
                "name": "Contact 2",
                "parent_id": company.id,
                "city": company.city,
                "state_id": company.state_id.id,
                "zip": company.zip,
                "country_id": self.country_th.id,
            }
        )
        self.assertEqual(contact2.type, "contact")
        self.assertEqual(contact2.l10n_th_subdistrict_id, self.subdistrict_tha_raeng)
        # The form copies the address of the company, with its own zip
        company.zip = "99999"
        with Form(
            self.env["res.partner"].with_context(default_parent_id=company.id)
        ) as contact_form:
            contact_form.name = "Contact 3"
            self.assertEqual(contact_form.zip, "99999")
        contact3 = contact_form.record
        self.assertEqual(contact3.type, "contact")
        self.assertEqual(contact3.zip, "99999")
        self.assertEqual(contact3.l10n_th_subdistrict_id, self.subdistrict_tha_raeng)
        # Foreign contacts are written as usual with the Thai ones
        foreign = self.env["res.partner"].create(
            {"name": "Foreign", "country_id": self.env.ref("base.us").id}
        )
        (company | foreign).write({"city": "Somewhere"})
        self.assertFalse(company.city_id)
        self.assertEqual(foreign.city, "Somewhere")

    def test_09_subdistrict_form(self):
        """The form fills the address when selecting a sub-district"""
        with Form(self.env["res.partner"]) as partner_form:
            partner_form.name = "Thai Partner"
            partner_form.country_id = self.country_th
            partner_form.l10n_th_subdistrict_id = self.subdistrict_palace
            self.assertEqual(partner_form.city_id, self.subdistrict_palace.city_id)
            self.assertEqual(partner_form.city, "แขวงพระบรมมหาราชวัง เขตพระนคร")
            self.assertEqual(partner_form.state_id, self.state_bangkok)
            self.assertEqual(partner_form.zip, "10200")
            partner_form.city_id = self.city_dusit
            self.assertFalse(partner_form.l10n_th_subdistrict_id)
            self.assertEqual(partner_form.city, "เขตดุสิต")
        partner = partner_form.record
        self.assertEqual(partner.city_id, self.city_dusit)
        self.assertEqual(partner.city, "เขตดุสิต")
        # A manual city detaches the district, before saving too
        with Form(partner) as partner_form:
            partner_form.l10n_th_subdistrict_id = self.subdistrict_palace
            partner_form.city = "Manual city"
            self.assertFalse(partner_form.city_id)
            self.assertFalse(partner_form.l10n_th_subdistrict_id)
        self.assertEqual(partner.city, "Manual city")
        self.assertFalse(partner.city_id)
        # Clearing the sub-district, then the district, keeps the address
        with Form(partner) as partner_form:
            partner_form.l10n_th_subdistrict_id = self.subdistrict_palace
        with Form(partner) as partner_form:
            partner_form.l10n_th_subdistrict_id = self.env[
                "l10n_th.res.city.subdistrict"
            ]
            self.assertEqual(partner_form.city, "เขตพระนคร")
        with Form(partner) as partner_form:
            partner_form.city_id = self.env["res.city"]
            self.assertEqual(partner_form.city, "เขตพระนคร")
            self.assertEqual(partner_form.zip, "10200")
        self.assertFalse(partner.city_id)
        self.assertEqual(partner.city, "เขตพระนคร")

    def test_10_subdistrict_display_name(self):
        """The sub-district shows its district and province in the dropdowns"""
        subdistrict = self.subdistrict_palace
        self.assertEqual(subdistrict.display_name, "พระบรมมหาราชวัง")
        formatted = subdistrict.with_context(formatted_display_name=True)
        self.assertEqual(
            formatted.display_name,
            f"พระบรมมหาราชวัง \v--พระนคร, {self.state_bangkok.name}--",
        )
        # As sent by the many2one field of the contact form
        result = formatted.name_search("พระบรมมหาราชวัง", limit=1)
        self.assertEqual(result, [(subdistrict.id, formatted.display_name)])
        # The district changes: the name follows
        subdistrict.sudo().city_id = self.city_dusit
        self.assertEqual(
            formatted.display_name,
            f"พระบรมมหาราชวัง \v--ดุสิต, {self.state_bangkok.name}--",
        )
        # A district without province is shown alone
        self.city_dusit.sudo().state_id = False
        self.assertEqual(formatted.display_name, "พระบรมมหาราชวัง \v--ดุสิต--")
        # Not yet in a district: the name only
        new_subdistrict = formatted.new({"name": "ใหม่"})
        self.assertEqual(new_subdistrict.display_name, "ใหม่")
