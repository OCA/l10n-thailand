# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

import requests

from odoo.exceptions import UserError
from odoo.tests import Form, common

logger = logging.getLogger(__name__)


class TestBaseLocation(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.thailand = self.env.ref("base.th")
        self.belgium = self.env.ref("base.be")
        self.Company = self.env["res.company"]
        self.Partner = self.env["res.partner"]
        self.zip_id = self.env["res.city.zip"]
        self.import_th_lang_th = (
            self.env["city.zip.geonames.import"]
            .with_context(import_test=True)
            .create(
                {
                    "country_ids": [(6, 0, [self.thailand.id])],
                    "location_thailand_language": "th",
                }
            )
        )
        self.import_th_lang_en = (
            self.env["city.zip.geonames.import"]
            .with_context(import_test=True)
            .create(
                {
                    "country_ids": [(6, 0, [self.thailand.id])],
                    "location_thailand_language": "en",
                }
            )
        )
        self.import_th_lang_th.run_import()
        self.import_th_lang_en.run_import()

    def test_01_import_base_location_th(self):
        """Test Import Thailand Location"""
        Wizard = self.env["city.zip.geonames.import"].create(
            {
                "country_ids": [(6, 0, [self.thailand.id])],
                "location_thailand_language": "th",
            }
        )
        self.assertTrue(Wizard.is_thailand)
        state_count = self.env["res.country.state"].search_count(
            [("country_id", "=", self.thailand.id)]
        )
        self.assertTrue(state_count)

    def test_02_import_not_th(self):
        """Test Import NOT Thailand Location"""
        import_be = (
            self.env["city.zip.geonames.import"]
            .with_context(import_test=True)
            .create(
                {
                    "country_ids": [(6, 0, [self.belgium.id])],
                    "location_thailand_language": "th",
                }
            )
        )
        try:
            with self.assertRaises(UserError):
                import_be.run_import()
        except requests.exceptions.ConnectionError as e:
            logger.exception("Connection Error: " + str(e))
        except Exception:
            import_be.run_import()

    def test_03_onchange_zip_id(self):
        """Test select zip_id in res_partner and res_company"""
        city_zip = self.zip_id.search(
            [("city_id.country_id", "=", self.thailand.id)], limit=1
        )
        address = city_zip.city_id.name.split(", ")
        # partner
        partner = Form(self.env["res.partner"])
        partner.zip_id = city_zip
        self.assertEqual(partner.zip, city_zip.name)
        self.assertEqual(partner.street2, address[0])
        self.assertEqual(partner.city, address[1])
        self.assertEqual(partner.state_id, city_zip.city_id.state_id)
        self.assertEqual(partner.country_id, city_zip.city_id.country_id)
        # company
        company = self.Company.new({"zip_id": city_zip.id})
        company._onchange_zip_id()
        self.assertEqual(company.street2, address[0])
        self.assertEqual(company.city, address[1])

    def test_04_th_address(self):
        """Test name_get() for Thai address"""
        state_id = self.env["res.country.state"].search([("name", "like", "กรุงเทพ")])
        record = self.env["res.partner"].create(
            {
                "name": "ทำเนียบรัฐบาล",
                "street": "1 ถนนนครปฐม",
                "street2": "แขวงถนนนครไชยศรี",
                "city": "เขตดุสิต",
                "state_id": state_id.id,
            }
        )
        name = record.state_id.name_get()
        self.assertNotEqual(name[0][1][-4:], "(TH)")

    def test_05_us_address(self):
        """Test name_get() for USA address"""
        state_id = self.env["res.country.state"].search([("code", "=", "NY")])
        record = self.env["res.partner"].create(
            {
                "name": "United Nations Headquarters",
                "street": "405 East 42nd Street",
                "street2": "",
                "city": "New York",
                "state_id": state_id.id,
            }
        )
        name = record.state_id.name_get()
        self.assertEqual(name[0][1][-4:], "(US)")
