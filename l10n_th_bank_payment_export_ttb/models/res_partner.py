# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ttb_advise_mode = fields.Selection(
        selection=[
            ("FAX", "Fax"),
            ("EMAIL", "Email"),
            ("SMS", "SMS"),
        ],
        string="Advise Mode",
    )
    ttb_fax = fields.Char(string="Beneficiary's Fax", size=50)
    ttb_email = fields.Char(string="Beneficiary's Email", size=50)
    ttb_sms = fields.Char(string="Beneficiary's SMS", size=50)
    ttb_fee_charge = fields.Selection(
        selection=[
            ("OUR", "OUR - Company"),
            ("BEN", "BEN - Beneficiary"),
        ],
        string="Fee Charge",
    )
    ttb_proxy_type = fields.Selection(
        selection=[
            ("MOB", "MOB - Mobile No."),
            ("TAX", "TAX - Tax ID"),
            ("NAT", "NAT - National ID"),
            ("EWALLET", "E-Wallet"),
        ],
        string="Proxy Type (Promtpay)",
    )
    ttb_proxy_value = fields.Char(string="Proxy Value", size=100)
