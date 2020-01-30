# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    alley = fields.Char(
        string="Alley", compute="_compute_address", inverse="_inverse_alley"
    )
    moo = fields.Char(string="Moo", compute="_compute_address", inverse="_inverse_moo")
    tambon_id = fields.Many2one(
        "res.tambon",
        string="Tambon/Khwaeng",
        track_visibility="always",
        compute="_compute_address",
        inverse="_inverse_tambon",
    )
    amphur_id = fields.Many2one(
        "res.amphur",
        string="Amphur/Khet",
        track_visibility="always",
        compute="_compute_address",
        inverse="_inverse_amphur",
    )
    province_id = fields.Many2one(
        "res.province",
        string="Province",
        track_visibility="always",
        compute="_compute_address",
        inverse="_inverse_province",
    )
    zip_id = fields.Many2one(
        "res.zip",
        string="Zip",
        track_visibility="always",
        compute="_compute_address",
        inverse="_inverse_zip_thai",
    )
    branch_code = fields.Char(
        string="Branch Code",
        compute="_compute_address",
        inverse="_inverse_branch_code",
        size=5,
    )

    def _get_company_address_fields(self, partner):
        return {
            "street": partner.street,
            "street2": partner.street2,
            "city": partner.city,
            "zip": partner.zip,
            "state_id": partner.state_id,
            "country_id": partner.country_id,
            "alley": partner.alley,
            "moo": partner.moo,
            "tambon_id": partner.tambon_id,
            "amphur_id": partner.amphur_id,
            "province_id": partner.province_id,
            "zip_id": partner.zip_id,
            "branch_code": partner.branch_code,
        }

    def _inverse_alley(self):
        for rec in self:
            rec.partner_id.alley = rec.alley

    def _inverse_moo(self):
        for rec in self:
            rec.partner_id.moo = rec.moo

    def _inverse_tambon(self):
        for rec in self:
            rec.partner_id.tambon_id = rec.tambon_id

    def _inverse_amphur(self):
        for rec in self:
            rec.partner_id.amphur_id = rec.amphur_id

    def _inverse_province(self):
        for rec in self:
            rec.partner_id.province_id = rec.province_id

    def _inverse_zip_thai(self):
        for rec in self:
            rec.partner_id.zip_id = rec.zip_id

    def _inverse_branch_code(self):
        for rec in self:
            rec.partner_id.branch_code = rec.branch_code

    @api.onchange("branch_code")
    def _onchange_branch_code(self):
        if self.branch_code is not False:
            regex = r"^[-+]?[0-9]+$"
            if len(self.branch_code) <= 5:
                branch_code = re.findall(regex, self.branch_code)
                if branch_code or branch_code is None:
                    pass
                else:
                    raise ValidationError(_("Branch Code Must be 5 Digits"))

    @api.onchange("moo")
    def _onchange_moo(self):
        if self.moo is not False:
            regex = r"^[-+]?[0-9]+$"
            if len(self.moo) <= 5:
                moo = re.findall(regex, self.moo)
                if moo or moo is None:
                    pass
                else:
                    raise ValidationError(_("Moo Must be digits only"))
