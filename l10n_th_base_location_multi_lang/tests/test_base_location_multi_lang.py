# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import common

from ..hooks import post_init_hook


class TestBaseLocationMultiLang(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thailand = cls.env.ref("base.th")
        cls.Partner = cls.env["res.partner"]
        cls.CityZip = cls.env["res.city.zip"]
        wizard = (
            cls.env["city.zip.geonames.import"]
            .with_context(import_test=True)
            .create(
                {
                    "country_ids": [(6, 0, [cls.thailand.id])],
                    "location_thailand_language": "th",
                }
            )
        )
        wizard.run_import()
        cls.city_zip = cls.CityZip.search(
            [("sub_district_code", "=", "100101")], limit=1
        )

    def test_01_import_fill_name_en(self):
        self.assertTrue(self.city_zip)
        self.assertEqual(self.city_zip.subdistrict_en, "Phra Borom Maha Ratchawang")
        self.assertEqual(self.city_zip.district_en, "Phra Nakhon")
        self.assertEqual(self.city_zip.state_en, "Bangkok")

    def test_02_partner_address_en(self):
        partner = self.Partner.create(
            {
                "name": "Test Partner",
                "country_id": self.thailand.id,
                "zip_id": self.city_zip.id,
            }
        )
        self.assertEqual(partner.subdistrict_en, "Phra Borom Maha Ratchawang")
        self.assertEqual(partner.district_en, "Phra Nakhon")
        self.assertEqual(partner.state_en, "Bangkok")
        partner.district_en = "Manual District"
        self.assertEqual(partner.district_en, "Manual District")
        child = self.Partner.create(
            {"name": "Child", "parent_id": partner.id, "type": "contact"}
        )
        self.assertEqual(child.subdistrict_en, "Phra Borom Maha Ratchawang")
        self.assertEqual(child.district_en, "Manual District")

    def test_03_post_init_hook(self):
        self.city_zip.write(
            {"subdistrict_en": False, "district_en": False, "state_en": False}
        )
        post_init_hook(self.env.cr, self.env.registry)
        self.assertEqual(self.city_zip.subdistrict_en, "Phra Borom Maha Ratchawang")
