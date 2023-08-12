# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    acc_holder_name_en = fields.Char(
        string="Account Holder Name (EN)",
        help="Account holder name, in case it is bank bahtnet",
    )
