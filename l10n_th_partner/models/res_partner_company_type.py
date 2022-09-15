# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class ResPartnerCompanyType(models.Model):
    _inherit = "res.partner.company.type"

    prefix = fields.Char(translate=True)
    suffix = fields.Char(translate=True)
    use_prefix_suffix = fields.Boolean(
        default=True,
        help="Select this field for compute partner name with prefix or suffix.",
    )
