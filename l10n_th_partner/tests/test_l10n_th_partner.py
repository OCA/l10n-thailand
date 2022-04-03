# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import Form, TransactionCase


class TestL10nThPartner(TransactionCase):
    def setUp(self):
        super(TestL10nThPartner, self).setUp()
        self.main_company = self.env.ref("base.main_company")
        self.create_title()
        self.create_original("Firstname", "Lastname")

    def create_title(self):
        self.title = self.env["res.partner.title"].create(
            {"name": "Miss", "shortcut": "Miss"}
        )

    def create_original(self, firstname, lastname):
        with Form(self.env["res.users"], view="base.view_users_form") as f:
            f.firstname = firstname
            f.lastname = lastname
            f.login = firstname
        self.user = f.save()

    def test_partner_company(self):
        """Test that you change company_type"""
        partner = self.user.partner_id
        partner.email = "test"
        partner.title = self.title
        self.assertEqual(partner.name, "Firstname Lastname")
        self.assertEqual(partner.display_fullname, "Miss Firstname Lastname")
        self.assertEqual(partner.title, self.title)
        partner.company_type = "company"
        partner._onchange_company_type()
        self.assertNotEqual(partner.title, self.title)
        # title on display fullname will remove
        self.assertEqual(partner.name, "Firstname Lastname")
        self.assertEqual(partner.display_fullname, "Firstname Lastname")

    def test_user_individual(self):
        """Test add title in individual"""
        # Standard Odoo
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.assertEqual(self.user.display_name, "Firstname Lastname")
        self.user.title = self.title
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.assertEqual(self.user.display_fullname, "Miss Firstname Lastname")
        # Config no space title
        self.main_company.no_space_title_name = True
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.assertEqual(self.user.display_name, "Firstname Lastname")
        self.user.title = self.title
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.assertEqual(self.user.display_fullname, "MissFirstname Lastname")
