# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TaxBranchOperatingUnit(models.Model):
    _name = "tax.branch.operating.unit"
    _description = "Tax Branch Operating Unit"

    name = fields.Char(
        string="Tax Branch",
        help="Branch ID, e.g., 0000, 0001, ...",
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "Tax Branch must be unique!"),
    ]
