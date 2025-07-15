# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ktb_email = fields.Char(string="Receiver's Email", size=40)
    ktb_sms = fields.Char(string="Receiver's SMS", size=20)
