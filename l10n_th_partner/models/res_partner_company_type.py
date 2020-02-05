# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ResPartnerCompanyType(models.Model):
    _inherit = "res.partner.company.type"

    prefix = fields.Char(string="Prefix", translate=True)
    suffix = fields.Char(string="Suffix", translate=True)
