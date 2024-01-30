# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    scb_beneficiary_noti = fields.Selection(
        selection=[
            ("N", "N - None"),
            ("F", "F - Fax"),
            ("S", "S - SMS"),
            ("E", "E - Email"),
        ],
        default="N",
        string="Beneficiary Notification",
    )
    # Support outward remittance
    scb_email_partner = fields.Char(string="Default Email", size=100)
    scb_phone_partner = fields.Char(string="Default Fax", size=10)
    scb_sms_partner = fields.Char(string="Default SMS", size=10)
    # Outward Remittance
    scb_customer_ref1 = fields.Char(
        string="Customer Ref1",
        size=32,
    )
    scb_customer_ref2 = fields.Char(
        string="Customer Ref2",
        size=32,
    )
