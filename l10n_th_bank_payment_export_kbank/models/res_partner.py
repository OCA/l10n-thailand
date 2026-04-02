# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    kbank_advice_mode = fields.Selection(
        selection=[
            ("F", "Fax"),
            ("E", "Email"),
        ],
        string="KBank Advice Mode",
    )
    kbank_fax = fields.Char(string="KBank Fax")
    kbank_email = fields.Char(string="KBank Email")
    kbank_sms = fields.Char(string="KBank SMS")
    kbank_sms_lang = fields.Selection(
        selection=[
            ("TH", "Thai"),
            ("EN", "English"),
        ],
        string="KBank SMS Language",
    )
