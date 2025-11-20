# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestTaxAddress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.partner.vat = ""
        cls.partner.branch = ""

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

    @patch(
        "odoo.addons.l10n_th_tax_address.models.res_partner.ResPartner.get_result_tax_address"
    )
    def test_02_tax_address(self, mock_get_result):
        """Test with Ecosoft tax id"""
        # Mock the API response
        mock_get_result.return_value = {
            "street": "459/132 หมู่บ้าน โครงการ นิว ไฮบ์ สุขสวัสดิ์ ถนนสุขสวัสดิ์",
            "street2": "แขวงราษฎร์บูรณะ",
            "city": "เขตราษฎร์บูรณะ",
            "state_id": False,
            "zip": "10140",
        }

        self.partner.vat = "0105554048641"
        self.partner.branch = "00000"

        # Check demo data before call api
        self.assertEqual(self.partner.street, "4557 De Silva St")

        self.partner.action_get_address()

        # Check demo data after call api
        self.assertEqual(
            self.partner.street,
            "459/132 หมู่บ้าน โครงการ นิว ไฮบ์ สุขสวัสดิ์ ถนนสุขสวัสดิ์",
        )
        self.assertEqual(self.partner.street2, "แขวงราษฎร์บูรณะ")
        self.assertEqual(self.partner.city, "เขตราษฎร์บูรณะ")
        # False because not found.
        # if create master data it will return 'กรุงเทพมหานคร'
        self.assertEqual(self.partner.state_id.name, False)
        self.assertEqual(self.partner.zip, "10140")

    @patch(
        "odoo.addons.l10n_th_tax_address.models.res_partner.ResPartner.get_result_tax_address"
    )
    def test_03_tax_address_api_error(self, mock_get_result):
        """Test API error handling"""
        mock_get_result.side_effect = ValidationError("API Error")

        self.partner.vat = "0105554048641"
        self.partner.branch = "00000"

        with self.assertRaises(ValidationError):
            self.partner.action_get_address()

    @patch(
        "odoo.addons.l10n_th_tax_address.models.res_partner.ResPartner.get_result_tax_address"
    )
    def test_04_tax_address_with_state(self, mock_get_result):
        """Test with state_id present"""
        state = self.env["res.country.state"].create(
            {
                "name": "กรุงเทพมหานคร",
                "code": "BKK",
                "country_id": self.env.ref("base.th").id,
            }
        )

        mock_get_result.return_value = {
            "street": "123 Test Street",
            "street2": "Test District",
            "city": "Test City",
            "state_id": state.id,
            "zip": "10000",
        }

        self.partner.vat = "0105554048641"
        self.partner.branch = "00000"

        self.partner.action_get_address()

        self.assertEqual(self.partner.street, "123 Test Street")
        self.assertEqual(self.partner.state_id.id, state.id)
        self.assertEqual(self.partner.zip, "10000")
