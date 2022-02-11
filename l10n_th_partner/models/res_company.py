# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    branch = fields.Char(
        related="partner_id.branch", string="Tax Branch", readonly=False
    )
    no_space_title_name = fields.Boolean(
        string="No Space Title and Name",
        help="If checked, title and name will no space",
    )
