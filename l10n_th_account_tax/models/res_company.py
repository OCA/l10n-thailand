# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    customer_tax_invoice_number = fields.Selection(
        selection=[
            ("payment", "Customer Payment Number"),
            ("invoice", "Customer Invoice Number"),
        ],
        string="Customer Tax Invoice Number (Undue VAT)",
        default="payment",
        help="""It default running tax number by payment
        when user not select 'Tax Invoice Sequence' in taxes""",
    )
