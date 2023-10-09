# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class WithHoldingTaxReport(models.TransientModel):
    _inherit = "withholding.tax.report"

    operating_unit_ids = fields.Many2many(
        comodel_name="operating.unit",
        string="Operating Unit",
    )
    show_operating_unit = fields.Boolean(
        string="Show Operating Unit",
    )
    
    def _get_domain_wht(self):
        domain = super()._get_domain_wht()
        if not self.operating_unit_ids:
            return domain
        if len(self.operating_unit_ids) > 1:
            domain.append(("cert_id.operating_unit_id", "in", self.operating_unit_ids.ids))
        else:
            domain.append(("cert_id.operating_unit_id", "=", self.operating_unit_ids.id))
        return domain
