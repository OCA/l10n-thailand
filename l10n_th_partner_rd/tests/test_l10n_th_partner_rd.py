# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from unittest.mock import Mock, patch

import requests

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form
from odoo.tests.common import TransactionCase, new_test_user

REQUESTS_POST = "odoo.addons.l10n_th_partner_rd.models.res_partner.requests.post"
# Same as data/l10n_th_partner_rd_mapping_data.xml
DEFAULT_TEMPLATES = {
    "name": "{name}",
    "street": "{house_no} {building} {room} {floor} {village} {moo} {soi} {yaek} "
    "{road}",
    "street2": "{sub_district}",
    "city": "{district}",
    "state_id": "{province}",
    "zip": "{zip}",
}
RD_KEYS = (
    "vNID",
    "vtin",
    "vtitleName",
    "vName",
    "vSurname",
    "vBranchTitleName",
    "vBranchName",
    "vBranchNumber",
    "vBuildingName",
    "vFloorNumber",
    "vVillageName",
    "vRoomNumber",
    "vHouseNumber",
    "vMooNumber",
    "vSoiName",
    "vStreetName",
    "vThambol",
    "vAmphur",
    "vProvince",
    "vPostCode",
    "vBusinessFirstDate",
    "vYaek",
    "vmsgerr",
)


class TestL10nThPartnerRd(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Default mapping, whatever the database has been configured with
        Mapping = cls.env["l10n_th.partner.rd.mapping"]
        Mapping.with_context(active_test=False).search([]).unlink()
        Mapping.create(
            [
                {
                    "field_id": cls.env.ref(f"base.field_res_partner__{field}").id,
                    "template": template,
                }
                for field, template in DEFAULT_TEMPLATES.items()
            ]
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Ecosoft", "street": "4557 De Silva St"}
        )
        # Answer of the Revenue Department for Ecosoft (head office)
        cls.rd_ecosoft = {
            "vNID": "0105554048641",
            "vtitleName": "บริษัท",
            "vName": "อีโคซอฟต์ จำกัด",
            "vSurname": "-",
            "vBranchTitleName": "บริษัท",
            "vBranchName": "อีโคซอฟต์ จำกัด",
            "vBranchNumber": "0",
            "vBuildingName": "-",
            "vFloorNumber": "-",
            "vVillageName": "โครงการ นิว ไฮบ์ สุขสวัสดิ์",
            "vRoomNumber": "-",
            "vHouseNumber": "459/132",
            "vMooNumber": "-",
            "vSoiName": "-",
            "vStreetName": "สุขสวัสดิ์",
            "vThambol": "ราษฎร์บูรณะ",
            "vAmphur": "ราษฎร์บูรณะ",
            "vProvince": "กรุงเทพมหานคร",
            "vPostCode": "10140",
            "vBusinessFirstDate": "2554-11-07",
            "vYaek": "-",
        }

    def _rd_response(self, data):
        """Build a SOAP answer of the Revenue Department VAT service."""
        elements = "".join(
            f'<{key}><anyType xsi:type="xsd:string">{data[key]}</anyType></{key}>'
            if data.get(key)
            else f"<{key} />"
            for key in RD_KEYS
        )
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body>'
            '<ServiceResponse xmlns="https://rdws.rd.go.th/serviceRD3/vatserviceRD3">'
            f"<ServiceResult>{elements}</ServiceResult>"
            "</ServiceResponse></soap:Body></soap:Envelope>"
        ).encode()

    def _get_address(self, partner, content):
        """Click the button with a mocked service answering ``content``,
        return the mock to check the request."""
        with patch(REQUESTS_POST, return_value=Mock(content=content)) as post:
            partner.action_l10n_th_rd_get_address()
        return post

    def test_01_tax_address_check_constraint(self):
        # User who cannot edit the contact does not call the service
        reader = new_test_user(self.env, login="rd_reader", groups="base.group_user")
        with (
            patch(REQUESTS_POST) as post,
            self.assertRaises(AccessError),
        ):
            self.partner.with_user(reader).action_l10n_th_rd_get_address()
        post.assert_not_called()
        self.assertFalse(self.partner.vat)
        # No Tax ID
        with self.assertRaisesRegex(UserError, "13 digits"):
            self.partner.action_l10n_th_rd_get_address()
        # Not a Thai Tax ID
        self.partner.vat = "12345"
        with self.assertRaisesRegex(UserError, "13 digits"):
            self.partner.action_l10n_th_rd_get_address()
        # Tax ID unknown by the Revenue Department
        self.partner.vat = "1234567890123"
        not_found = {"vmsgerr": "ไม่พบข้อมูลที่ต้องการค้นหา &lt;br&gt; Data not found "}
        with self.assertRaisesRegex(UserError, "Data not found"):
            self._get_address(self.partner, self._rd_response(not_found))
        # Service unreachable, or answering garbage
        with (
            patch(REQUESTS_POST, side_effect=requests.ConnectionError("timeout")),
            self.assertRaisesRegex(UserError, "Cannot reach"),
        ):
            self.partner.action_l10n_th_rd_get_address()
        for content in (b"Service Unavailable", b"<html><body>Error</body></html>"):
            with self.assertRaisesRegex(UserError, "invalid answer"):
                self._get_address(self.partner, content)
        # Service URL removed from the system parameters
        self.env["ir.config_parameter"].set_str(
            "l10n_th_partner_rd.vat_service_url", False
        )
        with self.assertRaisesRegex(UserError, "URL"):
            self.partner.action_l10n_th_rd_get_address()
        # No field mapping
        self.env["l10n_th.partner.rd.mapping"].search([]).active = False
        with self.assertRaisesRegex(UserError, "No field mapping"):
            self.partner.action_l10n_th_rd_get_address()
        self.assertEqual(self.partner.street, "4557 De Silva St")

    def test_02_tax_address(self):
        """Test with Ecosoft tax id and the default mapping"""
        self.partner.vat = "0105554048641"
        self.assertEqual(self.partner.street, "4557 De Silva St")

        post = self._get_address(self.partner, self._rd_response(self.rd_ecosoft))

        payload = post.call_args.kwargs["data"].decode()
        self.assertIn("<vat:TIN>0105554048641</vat:TIN>", payload)
        # No branch code means head office
        self.assertIn("<vat:BranchNumber>00000</vat:BranchNumber>", payload)
        self.assertEqual(self.partner.name, "บริษัท อีโคซอฟต์ จำกัด")
        self.assertEqual(
            self.partner.street,
            "459/132 หมู่บ้าน โครงการ นิว ไฮบ์ สุขสวัสดิ์ ถนนสุขสวัสดิ์",
        )
        # Bangkok uses แขวง/เขต instead of ต./อ.
        self.assertEqual(self.partner.street2, "แขวงราษฎร์บูรณะ")
        self.assertEqual(self.partner.city, "เขตราษฎร์บูรณะ")
        self.assertEqual(self.partner.state_id, self.env.ref("base.state_th_001"))
        self.assertEqual(self.partner.zip, "10140")
        self.assertEqual(self.partner.country_id, self.env.ref("base.th"))
        # Thai juristic person (Tax ID starts with 0)
        self.assertTrue(self.partner.is_company)
        # Branch Code of the answer
        self.assertEqual(
            self.partner._get_additional_identifier("TH_BRANCH_CODE"), "00000"
        )

        # Branch code of the standard partner identifiers is sent
        self.partner.additional_identifiers = {"TH_BRANCH_CODE": "00001"}
        branch_1 = dict(self.rd_ecosoft, vBranchNumber="1")
        post = self._get_address(self.partner, self._rd_response(branch_1))
        payload = post.call_args.kwargs["data"].decode()
        self.assertIn("<vat:BranchNumber>00001</vat:BranchNumber>", payload)
        self.assertEqual(
            self.partner._get_additional_identifier("TH_BRANCH_CODE"), "00001"
        )

    def test_03_tax_address_custom_mapping(self):
        """Fill the fields like the address form of Odoo l10n_th, keep the
        name and store the registration date"""
        Mapping = self.env["l10n_th.partner.rd.mapping"]
        Mapping.search([]).filtered(lambda m: m.field_id.name == "name").active = False
        templates = {
            "street": "{building} {room} {floor} {village}",
            "street2": "{house_no} {moo} {soi} {yaek} {road}",
            "city": "{sub_district} {district}",
        }
        for mapping in Mapping.search([]):
            if mapping.field_id.name in templates:
                mapping.template = templates[mapping.field_id.name]
        Mapping.create(
            {
                "field_id": self.env.ref("base.field_res_partner__ref").id,
                "template": "{vBusinessFirstDate}",
            }
        )
        chiang_mai = dict(
            self.rd_ecosoft,
            vBuildingName="ไอที",
            vFloorNumber="3",
            vRoomNumber="301",
            vVillageName="-",
            vHouseNumber="99",
            vMooNumber="5",
            vSoiName="-",
            vStreetName="ห้วยแก้ว",
            vThambol="สุเทพ",
            vAmphur="เมืองเชียงใหม่",
            vProvince="เชียงใหม่",
            vPostCode="50200",
        )
        self.partner.vat = "0105554048641"

        self._get_address(self.partner, self._rd_response(chiang_mai))

        self.assertEqual(self.partner.name, "Ecosoft")
        self.assertEqual(self.partner.street, "อาคาร ไอที ห้อง 301 ชั้น 3")
        self.assertEqual(self.partner.street2, "99 หมู่ที่ 5 ถนนห้วยแก้ว")
        self.assertEqual(self.partner.city, "ต.สุเทพ อ.เมืองเชียงใหม่")
        self.assertEqual(self.partner.state_id.name, "เชียงใหม่")
        self.assertEqual(self.partner.state_id.country_id, self.env.ref("base.th"))
        self.assertEqual(self.partner.zip, "50200")
        self.assertEqual(self.partner.ref, "2554-11-07")

        # Unknown province empties the state
        unknown = dict(chiang_mai, vProvince="ไม่มีจังหวัดนี้")
        self._get_address(self.partner, self._rd_response(unknown))
        self.assertFalse(self.partner.state_id)

    def test_04_mapping_constraint(self):
        with self.assertRaisesRegex(ValidationError, "only text and many2one"):
            self.env["l10n_th.partner.rd.mapping"].create(
                {
                    "field_id": self.env.ref("base.field_res_partner__active").id,
                    "template": "{name}",
                }
            )

    def test_05_tax_address_new_contact(self):
        """A new contact is filled when its Tax ID is typed, without a name"""
        head_office = Mock(content=self._rd_response(self.rd_ecosoft))
        branch_1 = dict(self.rd_ecosoft, vBranchNumber="1")
        branch = Mock(content=self._rd_response(branch_1))
        with patch(REQUESTS_POST, side_effect=[head_office, branch]) as post:
            with Form(self.env["res.partner"]) as form:
                form.vat = "0105554048641"
                self.assertEqual(form.name, "บริษัท อีโคซอฟต์ จำกัด")
                self.assertEqual(form.street2, "แขวงราษฎร์บูรณะ")
                self.assertEqual(form.city, "เขตราษฎร์บูรณะ")
                self.assertEqual(form.state_id, self.env.ref("base.state_th_001"))
                self.assertEqual(form.country_id, self.env.ref("base.th"))
                # Head office code set from the answer, without searching again
                branch_code = form.additional_identifiers["TH_BRANCH_CODE"]
                self.assertEqual(branch_code, "00000")
                self.assertEqual(post.call_count, 1)
                # Branch code typed after the Tax ID searches again
                form.additional_identifiers = {"TH_BRANCH_CODE": "00001"}
            partner = form.record
            self.assertEqual(post.call_count, 2)
            payload = post.call_args.kwargs["data"].decode()
            self.assertIn("<vat:BranchNumber>00001</vat:BranchNumber>", payload)
            self.assertEqual(partner.name, "บริษัท อีโคซอฟต์ จำกัด")
            self.assertEqual(partner.zip, "10140")
            self.assertEqual(
                partner._get_additional_identifier("TH_BRANCH_CODE"), "00001"
            )

            # Saved contacts use the button, foreign ones are never searched
            post.reset_mock()
            with Form(partner) as form:
                form.vat = "0105554048641 "
            with Form(self.env["res.partner"]) as form:
                form.name = "US company"
                form.country_id = self.env.ref("base.us")
                form.vat = "0105554048641"
            post.assert_not_called()

        # Errors of the service do not block the form
        not_found = {"vmsgerr": "ไม่พบข้อมูลที่ต้องการค้นหา &lt;br&gt; Data not found "}
        response = Mock(content=self._rd_response(not_found))
        with (
            patch(REQUESTS_POST, return_value=response),
            self.assertLogs("odoo.tests.form.onchange", "WARNING") as logs,
        ):
            form = Form(self.env["res.partner"])
            form.vat = "1234567890123"
        self.assertIn("Data not found", logs.output[0])
        self.assertFalse(form.name)
