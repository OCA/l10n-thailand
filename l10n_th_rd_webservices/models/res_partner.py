# Copyright 2020 Poonlap V. <poonlap@tanabutr.co.th>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import api, fields, models, exceptions, _

from zeep import Client, Transport, helpers
import requests
from requests import Session
from os import path
from pathlib import Path
import re
import pprint
from collections import OrderedDict

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    branch = fields.Char(string="Tax Branch", help="Branch ID, e.g., 0000, 0001, ...", default='00000')



    @staticmethod
    def check_rd_tin_service(tin):
        """Return bool after verifiying Tax Identification Number (TIN) or Personal Identification Number (PIN) 
           by using Revenue Department's web service to prevent forging.
           :param tin: a string for TIN or PIN
        """

        tin_web_service_url = "https://rdws.rd.go.th/serviceRD3/checktinpinservice.asmx?wsdl"
        sess = Session()
        mod_dir = path.dirname(path.realpath(__file__))
        cert_path = str(Path(mod_dir).parents[0]) + '/static/cert/adhq1_ADHQ5.cer'
        sess.verify = cert_path
        transp = Transport(session=sess)
        try:
            cl = Client(tin_web_service_url, transport=transp)
        except requests.exceptions.SSLError:
            _logger.log(logging.INFO, 'Fall back to unverifed HTTPS request.')
            sess.verify = False
            transp = Transport(session=sess)
            cl = Client(tin_web_service_url, transport=transp)
        result = cl.service.ServiceTIN('anonymous', 'anonymous', tin)
        res_ord_dict = helpers.serialize_object(result)
        _logger.log(logging.INFO, pprint.pformat( res_ord_dict))
        return res_ord_dict['vIsExist'] is not None

    @staticmethod
    def get_info_rd_vat_service(tin, branch = 0):
        """Return ordered dict with necessary result from Revenue Department's web service.
           :param tin: a string for TIN or PIN
           :param branch: one digit of branch number
        """
        branch = int(branch)
        vat_web_service_url = "https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx?wsdl"
        sess = Session()
        mod_dir = path.dirname(path.realpath(__file__))
        cert_path = str(Path(mod_dir).parents[0]) + '/static/cert/adhq1_ADHQ5.cer'
        sess.verify = cert_path
        transp = Transport(session=sess)
        try:
            cl = Client(vat_web_service_url, transport=transp)
        except requests.exceptions.SSLError:
            _logger.log(logging.INFO, 'Fall back to unverifed HTTPS request.')
            sess.verify = False
            transp = Transport(session=sess)
            cl = Client(vat_web_service_url, transport=transp)
        result = cl.service.Service(
            'anonymous',
            'anonymous',
            TIN=tin,
            ProvinceCode=0,
            BranchNumber=branch,
            AmphurCode=0,
        )
        odata = helpers.serialize_object(result)
        _logger.log(logging.INFO, pprint.pformat(odata))
        data = OrderedDict()
        if odata['vmsgerr'] is None:           
            for key, value in odata.items():
                if value is None or value['anyType'][0] == '-' or key in {'vNID', 'vtitleName','vName','vBusinessFirstDate'}:
                    continue
                data[key] = value['anyType'][0]
        _logger.log(logging.INFO, pprint.pformat( data ))
        return data
        

    __check_tin_re = re.compile(r'^\s*$|\d{13}')
    __check_branch_re = re.compile(r'^\s*$|\d{5}')
    @api.constrains('tax', 'branch')
    def _simple_validate(self):
        tin_match = self.__check_tin_re.match(self.vat) if self.vat is None else True
        branch_match = self.__check_branch_re.match(self.branch)

        if not (tin_match and branch_match):
            raise exceptions.ValidationError(_("TIN (VAT) must be 13 digits and Branch number must be 5 digits."))

    @api.onchange
    def action_auto_fill_info(self):
        pass

    @api.onchange('vat')
    def _onchange_vat(self):
        _logger.log(logging.INFO, self.vat)
        word_map = {
            'vBuildingName' : 'อาคาร ',
            'vFloorNumber' : 'ชั้นที่ ',
            'vVillageName' : 'หมู่บ้าน ',
            'vRoomNumber' : 'ห้องเลขที่ ',
            'vHouseNumber' : 'เลขที่ ',
            'vMooNumber' : 'หมู่ที่ ',
            'vSoiName' : 'ซอย ',
            'vStreetName' : 'ถนน ',
            'vThambol' : 'ตำบล',
            'vAmphur' : 'อำเภอ',
            'vProvince' : 'จังหวัด',
            'vPostCode' : '',
        }
        map_street = ['vBuildingName', 'vRoomNumber', 'vFloorNumber', 'vHouseNumber','vStreetName', 'vSoiName' ]
        map_street2 = ['vThambol']
        map_city = ['vAmphur']
        map_state = ['vProvince']
        map_zip = ['vPostCode']

        if self.vat == False or len(self.vat) != 13:
            return {}
        else:
            if ResPartner.check_rd_tin_service(self.vat):
                data = ResPartner.get_info_rd_vat_service(self.vat, self.branch)
                street = ''
                for i in map_street:
                    if i in data.keys():
                        street += word_map[i] + data[i] + ' '
                thambol  = word_map['vThambol'] + data['vThambol'] if data['vProvince'] != 'กรุงเทพมหานคร' else 'แขวง' + data['vThambol']
                amphur  = word_map['vAmphur'] + data['vAmphur'] if data['vProvince'] != 'กรุงเทพมหานคร' else 'เขต' + data['vAmphur']
                self.update({
                    'name_company' : data['vBranchTitleName'] + ' ' + data['vBranchName'],
                    'street' : street,
                    'street2' : thambol,
                    'city' : amphur,
                    'zip' : data['vPostCode'],
                    # 'state' : data['vProvince']
                })
                # if data['vmsgerr'] is None:
                #     self.update({
                #         'name_company' : data['vtitleName'] + " " + data['vName'],
                #         'street' : data['vBuildingName'],
                #          })
            else:
                warning_mess = {
                    'title': _("The TIN %s is not valid." % self.vat),
                    'message': _("Connected to RD's web service and failed to verify TIN or PIN %s." % self.vat)
                }
                return {'warning': warning_mess}    

