# Copyright 2020 Poonlap V. <poonlap@tanabutr.co.th>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging
import pprint
import re
from collections import OrderedDict
from logging import DEBUG, INFO
from os import path
from pathlib import Path

import requests
from requests import Session
from zeep import Client, Transport, helpers

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"
    tin_web_service_url = (
        "https://rdws.rd.go.th/serviceRD3/checktinpinservice.asmx?wsdl"
    )
    vat_web_service_url = "https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx?wsdl"

    @staticmethod
    def check_rd_tin_service(tin):
        """Return bool after verifiying Tax Identification Number (TIN)
           or Personal Identification Number (PIN)
           by using Revenue Department's web service to prevent forging.
           :param tin: a string for TIN or PIN
        """

        sess = Session()
        mod_dir = path.dirname(path.realpath(__file__))
        cert_path = str(Path(mod_dir).parents[0]) + "/static/cert/adhq1_ADHQ5.cer"
        sess.verify = cert_path
        transp = Transport(session=sess)
        try:
            cl = Client(ResPartner.tin_web_service_url, transport=transp)
        except requests.exceptions.SSLError:
            _logger.log(INFO, "Fall back to unverifed HTTPS request.")
            sess.verify = False
            transp = Transport(session=sess)
            cl = Client(ResPartner.tin_web_service_url, transport=transp)
        result = cl.service.ServiceTIN("anonymous", "anonymous", tin)
        res_ord_dict = helpers.serialize_object(result)
        _logger.log(DEBUG, pprint.pformat(res_ord_dict))
        return res_ord_dict["vIsExist"] is not None

    @staticmethod
    def get_info_rd_vat_service(tin, branch=0):
        """Return ordered dict with necessary result from
           Revenue Department's web service.
           :param tin: a string for TIN or PIN
           :param branch: one digit of branch number
        """
        branch = int(branch)
        sess = Session()
        mod_dir = path.dirname(path.realpath(__file__))
        cert_path = str(Path(mod_dir).parents[0]) + "/static/cert/adhq1_ADHQ5.cer"
        sess.verify = cert_path
        transp = Transport(session=sess)
        try:
            cl = Client(ResPartner.vat_web_service_url, transport=transp)
        except requests.exceptions.SSLError:
            _logger.log(INFO, "Fall back to unverifed HTTPS request.")
            sess.verify = False
            transp = Transport(session=sess)
            cl = Client(ResPartner.vat_web_service_url, transport=transp)
        result = cl.service.Service(
            "anonymous",
            "anonymous",
            TIN=tin,
            ProvinceCode=0,
            BranchNumber=branch,
            AmphurCode=0,
        )
        odata = helpers.serialize_object(result)
        _logger.log(DEBUG, pprint.pformat(odata))
        data = OrderedDict()
        if odata["vmsgerr"] is None:
            for key, value in odata.items():
                if (
                    value is None
                    or value["anyType"][0] == "-"
                    or key in {"vNID", "vBusinessFirstDate"}
                ):
                    continue
                data[key] = value["anyType"][0]
            return data
        else:
            return False

    @api.onchange("vat", "branch")
    def _onchange_vat_branch(self):
        word_map = {
            "vBuildingName": "อาคาร ",
            "vFloorNumber": "ชั้นที่ ",
            "vVillageName": "หมู่บ้าน ",
            "vRoomNumber": "ห้องเลขที่ ",
            "vHouseNumber": "เลขที่ ",
            "vMooNumber": "หมู่ที่ ",
            "vSoiName": "ซอย ",
            "vStreetName": "ถนน ",
            "vThambol": "ต.",
            "vAmphur": "อ.",
            "vProvince": "จ.",
            "vPostCode": "",
        }
        map_street = [
            "vBuildingName",
            "vRoomNumber",
            "vFloorNumber",
            "vHouseNumber",
            "vStreetName",
            "vSoiName",
        ]
        map_street2 = ["vVillageName", "vMooNumber", "vThambol"]
        check_branch = re.compile(r"^\d{5}$")

        if self.vat is False:
            return {}
        if ResPartner.check_rd_tin_service(self.vat):
            if self.branch is False:
                self.branch = "00000"
            match = check_branch.match(self.branch)
            if match is None:
                warning_message = {
                    "title": _("Branch validation failed"),
                    "message": _("Branch number %s must be 5 digits." % self.branch),
                }
                return {"warning": warning_message}
            data = ResPartner.get_info_rd_vat_service(self.vat, self.branch)
            _logger.log(DEBUG, pprint.pformat(data))
            if not data:
                warning_message = {
                    "title": _("Validation failed."),
                    "message": _(
                        "TIN %s is valid. Branch %s is not valid."
                        % (self.vat, self.branch)
                    ),
                }
                return {"warning": warning_message}
            if len(data) == 0:
                warning_message = {
                    "title": _("Can not get info from TIN" % self.vat),
                    "message": _("%s is valid but no address information." % self.vat),
                }
                return {"warning": warning_message}
            street = street2 = ""
            for i in map_street:
                if i in data.keys():
                    street += word_map[i] + data[i] + " "
            for i in map_street2:
                if i in data.keys():
                    if i == "vThambol":
                        street2 += (
                            word_map["vThambol"] + data["vThambol"] + " "
                            if data["vProvince"] != "กรุงเทพมหานคร"
                            else "แขวง" + data["vThambol"] + " "
                        )
                        continue
                    street2 += word_map[i] + data[i] + " "
            amphur = (
                word_map["vAmphur"] + data["vAmphur"]
                if data["vProvince"] != "กรุงเทพมหานคร"
                else "เขต" + data["vAmphur"]
            )
            province_id = self.env["res.country.state"].search(
                [["name", "ilike", data["vProvince"]]]
            )
            self.update(
                {
                    "name_company": data["vtitleName"] + " " + data["vName"],
                    "street": street,
                    "street2": street2,
                    "city": amphur,
                    "zip": data["vPostCode"],
                    "state_id": province_id,
                    "country_id": self.env.ref("base.th").id,
                }
            )
        else:
            warning_message = {
                "title": _("Validation failed."),
                "message": _("Failed to verify TIN or PIN %s." % self.vat),
            }
            return {"warning": warning_message}
