# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestL10nThPartner(TransactionCase):
    def setUp(self):
        super(TestL10nThPartner, self).setUp()
        self.create_title()
        self.create_original("Firstname", "Lastname")

    def create_title(self):
        self.title = self.env["res.partner.title"].create(
            {"name": "Miss", "shortcut": "Miss"}
        )

    def create_original(self, firstname, lastname):
        self.user = self.env["res.users"].create(
            {"firstname": firstname, "lastname": lastname, "login": firstname}
        )

    def test_res_users(self):
        """Test that you change title"""
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.user.title = self.title
        self.user._compute_name()
        self.assertEqual(self.user.name, "Miss Firstname Lastname")

    def test_res_partner(self):
        """Test that you change company_type"""
        partner = self.user.partner_id
        partner.email = "test"
        partner.title = self.title
        self.assertEqual(partner.title, self.title)
        partner.company_type = "company"
        partner._onchange_company_type()
        self.assertNotEqual(partner.title, self.title)
