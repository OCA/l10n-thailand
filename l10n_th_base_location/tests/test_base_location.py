# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.base_location.tests.test_base_location import TestBaseLocation

logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestTHBaseLocation(TestBaseLocation):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thailand = cls.env.ref("base.th")
        cls.belgium = cls.env.ref("base.be")
        cls.company_model = cls.env["res.company"]
        cls.partner_model = cls.env["res.partner"]
        cls.zip_id = cls.env["res.city.zip"]
        cls.country_state = cls.env["res.country.state"]
        cls.geonames_import_wizard = cls.env["city.zip.geonames.import"]

    def create_geonames_import(self, country, lang):
        import_wizard = self.geonames_import_wizard.with_context(max_import=10).create(
            {
                "country_ids": [Command.set([country.id])],
                "location_thailand_language": lang,
            }
        )
        import_wizard.run_import()
        return import_wizard

    def test_01_import_base_location_th(self):
        """Test Import Thailand Location"""
        country = self.country_state.search([("code", "=", "TH-10")], limit=1)
        country.unlink()
        import_wizard = self.create_geonames_import(self.thailand, "th")
        self.assertTrue(import_wizard.is_thailand)

        # If thai language, it will show 'กรุงเทพมหานคร'
        state_id = self.country_state.search([("code", "=", "TH-10")], limit=1)
        record = self.partner_model.create(
            {
                "name": "ทำเนียบรัฐบาล",
                "street": "1 ถนนนครปฐม",
                "street2": "แขวงถนนนครไชยศรี",
                "city": "เขตดุสิต",
                "state_id": state_id.id,
            }
        )
        name = record.state_id.name_get()
        self.assertEqual(name[0][1], "กรุงเทพมหานคร")

        city_zip = self.zip_id.search(
            [("city_id.country_id", "=", self.thailand.id)], limit=1
        )
        address = city_zip.city_id.name.split(", ")
        # partner
        partner = Form(self.partner_model)
        partner.zip_id = city_zip
        self.assertEqual(partner.zip, city_zip.name)
        self.assertEqual(partner.street2, address[0])
        self.assertEqual(partner.city, address[1])
        self.assertEqual(partner.state_id, city_zip.city_id.state_id)
        self.assertEqual(partner.country_id, city_zip.city_id.country_id)
        # company
        company = self.company_model.new({"zip_id": city_zip.id})
        company._onchange_zip_id()
        self.assertEqual(company.street2, address[0])
        self.assertEqual(company.city, address[1])
        # Test import Thai location with EN language
        import_wizard = self.create_geonames_import(self.thailand, "en")
        # If thai language, it will show 'Bangkok'
        state_id = self.country_state.search([("code", "=", "TH-10")], limit=1)
        record = self.partner_model.create(
            {
                "name": "ทำเนียบรัฐบาล",
                "street": "1 ถนนนครปฐม",
                "street2": "แขวงถนนนครไชยศรี",
                "city": "เขตดุสิต",
                "state_id": state_id.id,
            }
        )
        name = record.state_id.name_get()
        self.assertEqual(name[0][1], "Bangkok")

    def test_02_import_not_th(self):
        """Test Import NOT Thailand Location"""
        import_wizard = self.create_geonames_import(self.belgium, "th")
        self.assertFalse(import_wizard.is_thailand)
