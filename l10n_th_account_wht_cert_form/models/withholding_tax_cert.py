# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    def _get_report_base_filename(self):
        self.ensure_one()
        return self.env._(
            "WHT Certificates - %(name)s",
            name=self.display_name or False,
        )

    def _compute_desc_type_other(self, lines, ttype, income_type):
        base_type_other = lines.filtered(
            lambda line: line.wht_cert_income_type in [income_type]
        ).mapped(ttype)
        base_type_other = [x or "" for x in base_type_other]
        desc = ", ".join(base_type_other)
        return desc

    def _group_wht_line(self, lines):
        groups = self.env["withholding.tax.cert.line"]._read_group(
            domain=[("id", "in", lines.ids)],
            groupby=["wht_cert_income_type"],
            aggregates=["base:sum", "amount:sum"],
        )
        return [
            {
                "wht_cert_income_type": wht_cert_income_type,
                "base": base_sum,
                "amount": amount_sum,
            }
            for wht_cert_income_type, base_sum, amount_sum in groups
        ]
