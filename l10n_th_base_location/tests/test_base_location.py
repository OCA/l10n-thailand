# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestBaseLocation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.thailand = self.env.ref("base.th")
        self.belgium = self.env.ref("base.be")
        self.Company = self.env["res.company"]
        self.Partner = self.env["res.partner"]
        self.zip_id = self.env["res.city.zip"]
        self.env["city.zip.geonames.import"].with_context({"import_test": True}).create(
            {
                "country_ids": [(6, 0, [self.thailand.id, self.belgium.id])],
                "location_thailand_language": "th",
            }
        ).run_import()

    def test_01_import_base_location_th(self):
        """Test Import Thailand Location"""
        Wizard = self.env["city.zip.geonames.import"].create(
            {
                "country_ids": [(6, 0, [self.thailand.id])],
                "location_thailand_language": "th",
            }
        )
        self.assertTrue(Wizard.is_thailand)
        Wizard = self.env["city.zip.geonames.import"].create(
            {
                "country_ids": [(6, 0, [self.belgium.id])],
                "location_thailand_language": "th",
            }
        )
        self.assertFalse(Wizard.is_thailand)
        state_count = self.env["res.country.state"].search_count(
            [("country_id", "=", self.thailand.id)]
        )
        self.assertTrue(state_count)

    def test_02_onchange_zip_id(self):
        """Test select zip_id in res_partner and res_company"""
        city_zip = self.zip_id.search(
            [("city_id.country_id", "=", self.thailand.id)], limit=1
        )
        address = city_zip.city_id.name.split(", ")
        # partner
        partner = self.Partner.new({"zip_id": city_zip.id})
        partner._onchange_zip_id()
        self.assertEqual(partner.street2, address[0])
        self.assertEqual(partner.city, address[1])
        # company
        company = self.Company.new({"zip_id": city_zip.id})
        company._onchange_zip_id()
        self.assertEqual(company.street2, address[0])
        self.assertEqual(company.city, address[1])
