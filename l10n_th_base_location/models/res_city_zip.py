# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCityZip(models.Model):
    _inherit = "res.city.zip"

    district_code = fields.Char(
        string="District Code", help="This field is Amphoe (District) code in Thailand"
    )
    sub_district_code = fields.Char(
        string="Sub-District Code",
        help="This field is Tambon (Sub-District) code in Thailand",
    )
