# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import requests
from zeep import Client, Transport

from odoo import _, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_result_tax_address(self, tax_id, branch):
        self.ensure_one()
        if not (tax_id and branch):
            raise ValidationError(_("Please provide Tax ID and Branch"))

        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("l10n_th.tax_address_api")
        )

        # Setting up the session and client
        session = requests.Session()
        session.verify = True
        transport = Transport(session=session)
        client = Client(base_url, transport=transport)

        # Calling the web service
        try:
            result = client.service.Service(
                username="anonymous",
                password="anonymous",
                TIN=tax_id,
                ProvinceCode=0,
                BranchNumber=int(branch.isnumeric() and branch or "0"),
                AmphurCode=0,
            )
        except Exception as e:
            raise ValidationError(_("Failed to call web service: %s") % str(e)) from e

        # Check if result contains error message
        if hasattr(result, "vmsgerr") and result.vmsgerr:
            raise ValidationError(", ".join(result.vmsgerr["anyType"]))

        # Convert result to dict
        data = {}
        for key in result:
            value = result[key]
            if value and "anyType" in value:
                any_type_list = value["anyType"]
                data[key] = any_type_list[0] if any_type_list else None
            else:
                data[key] = value

        return self.finalize_address_dict(data)

    def finalize_address_dict(self, data):
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
            # "vHouseNumber": "เลขที่",
            "vMooNumber": "หมู่ที่",
            "vSoiName": "ซอย",
            "vStreetName": "ถนน",
            "vThambol": "ต.",
            "vAmphur": "อ.",
            "vProvince": "จ.",
        }
        name = "{} {}".format(data.get("vtitleName"), data.get("vName"))
        if data.get("vSurname", "-") != "-":
            name = "{} {}".format(name, data["vSurname"])
        house = data.get("vHouseNumber", "")
        village = get_part(data, "vVillageName", "%s %s")
        soi = get_part(data, "vSoiName", "%s %s")
        moo = get_part(data, "vMooNumber", "%s %s")
        building = get_part(data, "vBuildingName", "%s %s")
        floor = get_part(data, "vFloorNumber", "%s %s")
        room = get_part(data, "vRoomNumber", "%s %s")
        street = get_part(data, "vStreetName", "%s%s")
        thambon = get_part(data, "vThambol", "%s%s")
        get_part(data, "vAmphur", "%s%s")
        province = get_part(data, "vProvince", "%s%s")
        postal = data.get("vPostCode", "")

        if province == "จ.กรุงเทพมหานคร":
            thambon = data.get("vThambol") and "แขวง%s" % data["vThambol"] or ""
            amphur = data.get("vAmphur") and "เขต%s" % data["vAmphur"] or ""
            province = data.get("vProvince") and "%s" % data["vProvince"] or ""

        # Convert province name to state_id
        province_id = self.env["res.country.state"].search([("name", "=", province)])

        address_parts = filter(
            lambda x: x != "", [house, village, soi, moo, building, floor, room, street]
        )
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
