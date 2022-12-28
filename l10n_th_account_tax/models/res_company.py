# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    undue_output_name_config = fields.Selection(
        [
            ("payment", "Payment"),
            ("invoice", "Invoice"),
        ],
        default="payment",
        string="Undue Tax Invoices Number",
        help="The customer with the undue tax number will use the following configuration",
    )
