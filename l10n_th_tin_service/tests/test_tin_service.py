from odoo.tests import TransactionCase


class TestTinService(TransactionCase):
    def setUp(self):
        super(TestTinService, self).setUp()
        self.partner_obj = self.env["res.partner"]

    def test_tin_invalide_value(self):
        """Test a invalid TIN."""
        tin = "1111111111111"
        self.assertFalse(self.partner_obj.check_rd_tin_service(tin))

    def test_tin_valid_value(self):
        """Test a valid TIN."""
        tin = "0105519005906"
        self.assertTrue(self.partner_obj.check_rd_tin_service(tin))

    def test_tin_info(self):
        """Test a known value from TIN number"""
        tin = "0105519005906"
        result_odict = self.partner_obj.get_info_rd_vat_service(tin)
        self.assertEqual(result_odict["vName"], "ธนาบุตร จำกัด")

    def test_partner_on_change(self):
        """Test onchange"""
        partner = self.partner_obj.create(
            {"name": "Fake name", "company_type": "company", "vat": "0105519005906"}
        )
        partner._onchange_vat_branch()
        self.assertEqual("บริษัท ธนาบุตร จำกัด", partner.name_company)

    def test_partner_on_change_branch(self):
        partner = self.partner_obj.create(
            {
                "name": "Fake name",
                "company_type": "company",
                "vat": "0115558017774",
                "branch": "00000",
            }
        )
        partner._onchange_vat_branch()
        self.assertEqual("10330", partner.zip)
        partner.branch = "00001"
        partner._onchange_vat_branch()
        self.assertEqual("12130", partner.zip)
