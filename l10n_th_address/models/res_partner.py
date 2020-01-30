# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    alley = fields.Char(string="Alley")
    moo = fields.Char(string="Moo")
    tambon_id = fields.Many2one(
        "res.tambon", string="Tambon/Khwaeng", track_visibility="always"
    )
    amphur_id = fields.Many2one(
        "res.amphur", string="Amphur/Khet", track_visibility="always"
    )
    province_id = fields.Many2one(
        "res.province", string="Province", track_visibility="always"
    )
    zip_id = fields.Many2one("res.zip", string="Zip", track_visibility="always")
    branch_code = fields.Char(string="Branch Code", size=5)

    @api.onchange("email")
    def _onchange_check_email(self):
        if self.email is not False:
            regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

            email = re.findall(regex, self.email)
            if email or email is None:
                pass
            else:
                raise ValidationError(_("Email is invalid"))

    @api.onchange("branch_code")
    def _onchange_branch_code(self):
        if self.branch_code is not False:
            regex = r"^[-+]?[0-9]+$"
            if len(self.branch_code) <= 5:
                branch_code = re.findall(regex, self.branch_code)
                if branch_code or branch_code is None:
                    pass
                else:
                    raise ValidationError(_("Branch Code must be 5 digits"))

    @api.onchange("moo")
    def _onchange_moo(self):
        if self.moo is not False:
            regex = r"^[-+]?[0-9]+$"
            if len(self.moo) <= 5:
                moo = re.findall(regex, self.moo)
                if moo or moo is None:
                    pass
                else:
                    raise ValidationError(_("Moo must be digits only"))
