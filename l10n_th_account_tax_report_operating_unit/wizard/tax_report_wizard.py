# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TaxReportWizard(models.TransientModel):
    _inherit = "tax.report.wizard"

    operating_unit_ids = fields.Many2many(
        comodel_name="operating.unit",
        string="Operating Unit",
    )
    show_operating_unit = fields.Boolean(
        string="Show Operating Unit",
        default=True,
    )

    def _prepare_tax_report(self):
        res = super()._prepare_tax_report()
        res["show_operating_unit"] = self.show_operating_unit
        if self.operating_unit_ids:
            res["operating_unit_ids"] = [(6, 0, self.operating_unit_ids.ids)]
        return res

