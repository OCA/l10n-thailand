# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import Form, TransactionCase


class TestL10nThPartner(TransactionCase):
    def setUp(self):
        super(TestL10nThPartner, self).setUp()
        self.main_company = self.env.ref("base.main_company")
        self.create_title()
        self.create_original("Firstname", "Lastname")
        self.company_type = self.env.ref("l10n_th_partner.company_type_3")

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

    def test_res_users(self):
        """Test that you change title"""
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.user.title = self.title
        self.user._compute_name()
        self.assertEqual(self.user.name, "Miss Firstname Lastname")

    def test_res_partner(self):
        """Test all of partner individual"""
        partner = self.user.partner_id
        partner.email = "test"
        partner.title = self.title
        # change individual -> company
        self.assertEqual(partner.title, self.title)
        self.assertFalse(partner.name_company)
        with Form(partner) as p:
            p.company_type = "company"
            p.name_company = ("Test Company",)
        self.assertNotEqual(partner.title, self.title)
        self.assertTrue(partner.name_company)

    def test_res_partner_company(self):
        """Test all of partner company"""
        with Form(
            self.env["res.partner"], view="partner_firstname.view_partner_form"
        ) as f:
            f.company_type = "company"
            f.name_company = ("Test Company",)
            f.partner_company_type_id = self.company_type
        partner = f.save()
        # name include title, name_company not include title
        self.assertTrue(partner.name_company)
        self.assertNotEqual(partner.name, partner.name_company)

    def test_res_users_config_no_space(self):
        """Test that you change title and config title no space"""
        self.main_company.no_space_title_name = True
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.user.title = self.title
        self.assertEqual(self.user.name, "MissFirstname Lastname")
