# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class OperatingUnit(models.Model):
    _inherit = "operating.unit"

    tax_branch_id = fields.Many2one(
        comodel_name="tax.branch.operating.unit",
        index=True,
    )
