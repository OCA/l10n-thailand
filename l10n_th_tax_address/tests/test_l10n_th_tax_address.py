# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTaxAddress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_12")

    def test_01_tax_address_check_constraint(self):
        self.assertFalse(self.partner.vat)
        self.assertFalse(self.partner.branch)
        # No Tax ID, No Branch
        with self.assertRaises(ValidationError):
            self.partner.action_get_address()

        # No Branch
        self.partner.vat = "1234567890123"
        with self.assertRaises(ValidationError):
            self.partner.action_get_address()

        # Use demo tax, result contains error message
        # ไม่พบข้อมูลที่ต้องการค้นหา <br> Data not found
        self.partner.branch = "00000"
        with self.assertRaises(ValidationError):
            self.partner.action_get_address()

    def test_02_tax_address(self):
        """Test with Ecosoft tax id"""
        self.partner.vat = "0105554048641"
        self.partner.branch = "00000"

        # Check demo data before call api
        self.assertEqual(self.partner.street, "4557 De Silva St")

        self.partner.action_get_address()

        # Check demo data after call api
        self.assertEqual(
            self.partner.street, "281/19-23 อาคาร เอ็นเอสที วัน ชั้น 6 ห้อง 604 ถนนสีลม"
        )
        self.assertEqual(self.partner.street2, "แขวงสีลม")
        self.assertEqual(self.partner.city, "เขตบางรัก")
        # False because not found.
        # if create master data it will return 'กรุงเทพมหานคร'
        self.assertEqual(self.partner.state_id.name, False)
        self.assertEqual(self.partner.zip, "10500")
