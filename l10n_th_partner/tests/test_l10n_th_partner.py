# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import ValidationError
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

    def test_res_users_config_no_space(self):
        """Test that you change title and config title no space"""
        self.main_company.no_space_title_name = True
        self.assertEqual(self.user.name, "Firstname Lastname")
        self.user.title = self.title
        self.assertEqual(self.user.name, "MissFirstname Lastname")

    def test_duplicate_partner_vat_branch(self):
        partner1 = self.env["res.partner"].create(
            {
                "firstname": "Firstname",
                "lastname": "Lastname",
                "vat": "0123456789012",
                "branch": "00000",
                "company_id": self.main_company.id,
            }
        )
        partner2 = partner1.copy()
        with self.assertRaises(ValidationError):
            with Form(partner2) as p2:
                p2.branch = "00000"
