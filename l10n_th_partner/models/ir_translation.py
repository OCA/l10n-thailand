# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class IrTranslation(models.Model):
    _inherit = "ir.translation"

    def write(self, vals):
        res = super().write(vals)

        # Recompute name for res.partner
        recompute_fields = [
            "res.partner,name_company",
            "res.partner,firstname",
            "res.partner,lastname",
        ]
        for rec in self.filtered(
            lambda l: l.type == "model" and l.name in recompute_fields
        ):
            model = rec.name.split(",")[0]
            obj = (
                self.env[model]
                .with_context(
                    lang=rec.lang,
                    skip_inverse_name=True,
                )
                .browse(rec.res_id)
            )
            obj._compute_name()
            obj._compute_display_name()

        # Recompute name for hr.employee's name",
        for rec in self.filtered(
            lambda l: l.type == "model" and l.name == "resource.resource,name"
        ):
            employee = self.env["hr.employee"].search(
                [("resource_id", "=", rec.res_id)]
            )
            employee.with_context(lang=rec.lang).name = vals.get("value")

        return res
