# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import re

import requests
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError

RD_SERVICE_URL_PARAM = "l10n_th_partner_rd.vat_service_url"
RD_SERVICE_TIMEOUT = 20
RD_HEAD_OFFICE = "00000"
RD_BANGKOK = "กรุงเทพมหานคร"
RD_SOAP_PAYLOAD = (
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
    'xmlns:vat="https://rdws.rd.go.th/serviceRD3/vatserviceRD3">'
    "<soap:Header/>"
    "<soap:Body>"
    "<vat:Service>"
    "<vat:username>anonymous</vat:username>"
    "<vat:password>anonymous</vat:password>"
    "<vat:TIN>{tin}</vat:TIN>"
    "<vat:Name></vat:Name>"
    "<vat:ProvinceCode>0</vat:ProvinceCode>"
    "<vat:BranchNumber>{branch}</vat:BranchNumber>"
    "<vat:AmphurCode>0</vat:AmphurCode>"
    "</vat:Service>"
    "</soap:Body>"
    "</soap:Envelope>"
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Tax ID and Branch Code searched by the onchange in the current request,
    # so that setting the Branch Code from the answer does not search again
    l10n_th_rd_search_key = fields.Char(store=False, export_string_translation=False)

    @api.onchange("vat", "additional_identifiers")
    def _onchange_l10n_th_rd_get_address(self):
        """Fill a new contact as soon as its Tax ID is typed: the button
        needs a saved contact, hence a name."""
        tin = self._l10n_th_rd_get_tin()
        search_key = f"{tin}/{self._l10n_th_rd_get_branch()}"
        if (
            self._origin.id
            or (self.country_id and self.country_code != "TH")
            or len(tin) != 13
            or self.l10n_th_rd_search_key == search_key
        ):
            return None
        mappings = self._l10n_th_rd_get_mappings()
        if not mappings:
            return None
        self.l10n_th_rd_search_key = search_key
        try:
            data = self._l10n_th_rd_call_vat_service()
        except UserError as e:
            return {
                "warning": {
                    "title": self.env._("Revenue Department"),
                    "message": e.args[0],
                }
            }
        values = self._l10n_th_rd_prepare_template_values(data)
        self.update(self._l10n_th_rd_prepare_partner_vals(mappings, values))
        return None

    def action_l10n_th_rd_get_address(self):
        # Do not call the service for a user who cannot save its answer
        self.check_access("write")
        mappings = self._l10n_th_rd_get_mappings()
        if not mappings:
            raise UserError(
                self.env._(
                    "No field mapping is defined to fill contacts from the "
                    "Revenue Department."
                )
            )
        for partner in self:
            data = partner._l10n_th_rd_call_vat_service()
            values = partner._l10n_th_rd_prepare_template_values(data)
            partner.write(partner._l10n_th_rd_prepare_partner_vals(mappings, values))
        return True

    def _l10n_th_rd_get_mappings(self):
        return (
            self.env["l10n_th.partner.rd.mapping"]
            .sudo()
            .search([("field_id.model", "=", self._name)])
        )

    def _l10n_th_rd_get_tin(self):
        return re.sub(r"\D", "", self.vat or "")

    def _l10n_th_rd_get_branch(self):
        return self._get_additional_identifier("TH_BRANCH_CODE") or RD_HEAD_OFFICE

    def _l10n_th_rd_call_vat_service(self):
        """Search the Tax ID and Branch Code of the partner in the VAT service
        of the Revenue Department, return its answer as a dict."""
        self.ensure_one()
        tin = self._l10n_th_rd_get_tin()
        if len(tin) != 13:
            raise UserError(
                self.env._(
                    "The Tax ID of %(partner)s must have 13 digits to be searched "
                    "at the Revenue Department.",
                    partner=self.display_name,
                )
            )
        branch = self._l10n_th_rd_get_branch()
        url = self.env["ir.config_parameter"].sudo().get_str(RD_SERVICE_URL_PARAM)
        if not url:
            raise UserError(
                self.env._(
                    "The URL of the Revenue Department service is not set "
                    "(system parameter %(key)s).",
                    key=RD_SERVICE_URL_PARAM,
                )
            )
        try:
            response = requests.post(
                url,
                data=RD_SOAP_PAYLOAD.format(tin=tin, branch=branch).encode(),
                headers={"content-type": "application/soap+xml; charset=utf-8"},
                timeout=RD_SERVICE_TIMEOUT,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise UserError(
                self.env._(
                    "Cannot reach the Revenue Department service:\n%(error)s",
                    error=e,
                )
            ) from e
        data = self._l10n_th_rd_parse_response(response.content)
        if data.get("vmsgerr"):
            raise UserError(
                self.env._("Revenue Department: %(error)s", error=data["vmsgerr"])
            )
        return data

    @api.model
    def _l10n_th_rd_parse_response(self, content):
        """Return ``{key: value}`` from the ``ServiceResult`` of the SOAP answer,
        where each key element holds its value in an ``anyType`` child."""
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            root = etree.fromstring(content, parser=parser)
        except etree.XMLSyntaxError as e:
            raise UserError(
                self.env._("The Revenue Department service sent an invalid answer.")
            ) from e
        result = root.find(".//{*}ServiceResult")
        if result is None:
            raise UserError(
                self.env._("The Revenue Department service sent an invalid answer.")
            )
        data = {}
        for element in result:
            value = element.findtext("{*}anyType") or ""
            data[etree.QName(element).localname] = value.strip()
        return data

    def _l10n_th_rd_prepare_template_values(self, data):
        """Return the placeholders available to the field mapping templates:
        the raw keys of the service (``vHouseNumber``...) and keys formatted
        like a Thai address (``house_no``...). The service sends ``-`` for an
        empty value."""
        raw = {key: "" if value == "-" else value for key, value in data.items()}
        bangkok = raw.get("vProvince") == RD_BANGKOK

        def labeled(label, key, separator=" "):
            return raw.get(key) and f"{label}{separator}{raw[key]}" or ""

        name_parts = (
            raw.get("vBranchTitleName"),
            raw.get("vBranchName"),
            raw.get("vSurname"),
        )
        return {
            **raw,
            "name": " ".join(part for part in name_parts if part),
            "house_no": raw.get("vHouseNumber", ""),
            "building": labeled("อาคาร", "vBuildingName"),
            "room": labeled("ห้อง", "vRoomNumber"),
            "floor": labeled("ชั้น", "vFloorNumber"),
            "village": labeled("หมู่บ้าน", "vVillageName"),
            "moo": labeled("หมู่ที่", "vMooNumber"),
            "soi": labeled("ซอย", "vSoiName"),
            "yaek": labeled("แยก", "vYaek"),
            "road": labeled("ถนน", "vStreetName", separator=""),
            "sub_district": labeled(
                "แขวง" if bangkok else "ต.", "vThambol", separator=""
            ),
            "district": labeled("เขต" if bangkok else "อ.", "vAmphur", separator=""),
            "province": raw.get("vProvince", ""),
            "zip": raw.get("vPostCode", ""),
        }

    def _l10n_th_rd_prepare_partner_vals(self, mappings, values):
        self.ensure_one()
        vals = {
            mapping.field_id.name: mapping._get_partner_value(self, values)
            for mapping in mappings
        }
        # A partner registered at the Revenue Department is Thai
        vals.setdefault("country_id", self.env.ref("base.th").id)
        # Branch Code of the answer, 0 for the head office
        branch = values.get("vBranchNumber", "")
        identifiers = self.additional_identifiers or {}
        if branch.isdigit() and identifiers.get("TH_BRANCH_CODE") != branch.zfill(5):
            vals["additional_identifiers"] = {
                **identifiers,
                "TH_BRANCH_CODE": branch.zfill(5),
            }
        return vals
