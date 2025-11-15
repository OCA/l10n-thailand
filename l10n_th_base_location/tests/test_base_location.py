# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import requests

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.base_location_geonames_import.tests.test_base_location_geonames_import import (  # noqa: E501
    TestBaseLocationGeonamesImport,
)


@tagged("post_install", "-at_install")
class TestTHBaseLocation(TestBaseLocationGeonamesImport):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()

        cls.country_th = cls.env.ref("base.th")
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
        import_wizard = self.create_geonames_import(self.country_th, "th")
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
            [("city_id.country_id", "=", self.country_th.id)], limit=1
        )
        district = city_zip.city_id.name
        sub_district = city_zip.subdistrict_id.name
        # partner
        partner = Form(self.partner_model)
        partner.zip_id = city_zip
        self.assertEqual(partner.zip, city_zip.name)
        self.assertEqual(partner.subdistrict_id.name, sub_district)
        self.assertEqual(partner.city, district)
        self.assertEqual(partner.state_id, city_zip.city_id.state_id)
        self.assertEqual(partner.country_id, city_zip.city_id.country_id)
        # company
        with Form(self.company_model) as company_form:
            company_form.name = "Test New Company"
            company_form.zip_id = city_zip
        company = company_form.save()
        self.assertEqual(company.subdistrict_id.name, sub_district)
        self.assertEqual(company.city, district)
        # # Test import Thai location with EN language
        # import_wizard = self.create_geonames_import(self.country_th, "en")
        # # If thai language, it will show 'Bangkok'
        # state_id = self.country_state.search([("code", "=", "TH-10")], limit=1)
        # record = self.partner_model.create(
        #     {
        #         "name": "ทำเนียบรัฐบาล",
        #         "street": "1 ถนนนครปฐม",
        #         "street2": "แขวงถนนนครไชยศรี",
        #         "city": "เขตดุสิต",
        #         "state_id": state_id.id,
        #     }
        # )
        # name = record.state_id.name_get()
        # self.assertEqual(name[0][1], "Bangkok")
