# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    customer_tax_invoice_number = fields.Selection(
        [
            ("document", "Document Number"),
            ("invoice", "Invoice Number"),
        ],
        default="document",
        help="""It default running tax number by document
        when user not select 'Tax Invoice Sequence' in taxes""",
    )
