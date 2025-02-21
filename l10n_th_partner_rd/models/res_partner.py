# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import requests
from lxml import etree

from odoo import _, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_result_tax_address(self, tax_id, branch):
        self.ensure_one()
        if not (tax_id and branch):
            raise ValidationError(_("Please provide Tax ID and Branch"))

        # API Configuration
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("l10n_th.tax_address_api")
        )
        querystring = {"wsdl": ""}
        headers = {"content-type": "application/soap+xml; charset=utf-8"}

        # Prepare SOAP payload
        payload = (
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:vat="https://rdws.rd.go.th/serviceRD3/vatserviceRD3">'
            "<soap:Header/>"
            "<soap:Body>"
            "<vat:Service>"
            "<vat:username>anonymous</vat:username>"
            "<vat:password>anonymous</vat:password>"
            "<vat:TIN>{}</vat:TIN>"
            "<vat:Name></vat:Name>"
            "<vat:ProvinceCode>0</vat:ProvinceCode>"
            "<vat:BranchNumber>{}</vat:BranchNumber>"
            "<vat:AmphurCode>0</vat:AmphurCode>"
            "</vat:Service>"
            "</soap:Body>"
            "</soap:Envelope>"
        ).format(tax_id, branch)

        # Setup session with SSL verification disabled
        session = requests.Session()
        session.verify = False

        try:
            # Make the API request
            response = session.post(
                base_url, data=payload, headers=headers, params=querystring
            )
            response.raise_for_status()  # Raise exception for HTTP errors

            # Parse XML response
            result = etree.fromstring(response.content)

            # Process response data
            data = {}
            value = False
            for element in result.iter():
                tag = etree.QName(element).localname
                if not value and tag[:1] == "v":
                    value = tag
                    continue
                if value and tag == "anyType":
                    data[value] = element.text.strip()
                value = False

            if data.get("vmsgerr"):
                raise ValidationError(_(data.get("vmsgerr")))

            return self.finalize_address_dict(data)

        except requests.exceptions.RequestException as e:
            raise ValidationError(_("Request failed: %s") % str(e)) from e

    def finalize_address_dict(self, data):
        """Final processing of the received address data."""

        def get_part(data, key, value):
            return (
                data.get(key, "-") != "-"
                and value % (mapping_value[key], data.get(key))
                or ""
            )

        mapping_value = {
            "vBuildingName": "อาคาร",
            "vFloorNumber": "ชั้น",
            "vVillageName": "หมู่บ้าน",
            "vRoomNumber": "ห้อง",
            "vMooNumber": "หมู่ที่",
            "vSoiName": "ซอย",
            "vStreetName": "ถนน",
            "vThambol": "ต.",
            "vAmphur": "อ.",
            "vProvince": "จ.",
        }
        name = f"{data.get('vBranchTitleName')} {data.get('vBranchName')}"
        if "vSurname" in data and data["vSurname"] not in ("-", "", None):
            name = f"{name} {data['vSurname']}"
        house = data.get("vHouseNumber", "")
        village = get_part(data, "vVillageName", "%s %s")
        soi = get_part(data, "vSoiName", "%s %s")
        moo = get_part(data, "vMooNumber", "%s %s")
        building = get_part(data, "vBuildingName", "%s %s")
        floor = get_part(data, "vFloorNumber", "%s %s")
        room = get_part(data, "vRoomNumber", "%s %s")
        street = get_part(data, "vStreetName", "%s%s")
        thambon = get_part(data, "vThambol", "%s%s")
        amphur = get_part(data, "vAmphur", "%s%s")
        province = get_part(data, "vProvince", "%s%s")
        postal = data.get("vPostCode", "")

        if province == "จ.กรุงเทพมหานคร":
            thambon = data.get("vThambol") and f"แขวง{data['vThambol']}" or ""
            amphur = data.get("vAmphur") and f"เขต{data['vAmphur']}" or ""
            province = data.get("vProvince") and f"{data['vProvince']}" or ""

        address_parts = filter(
            lambda x: x != "", [house, village, soi, moo, building, floor, room, street]
        )

        # Convert province name to state_id
        province_id = self.env["res.country.state"].search([("name", "=", province)])

        return {
            "company_type": "company",
            "name_company": name,
            "street": " ".join(address_parts),
            "street2": thambon,
            "city": amphur,
            "state_id": province_id.id or False,
            "zip": postal,
        }

    def action_get_address(self):
        for rec in self:
            result = rec.get_result_tax_address(rec.vat, rec.branch)
            rec.write(result)
