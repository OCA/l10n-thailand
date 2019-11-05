# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from num2words import num2words

from odoo import api, models


class ReportWithholdingTaxCert(models.AbstractModel):
    _name = "report.withholding_tax_pdf"
    _description = "Withholding tax cert report with pdf preprint"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "withholding_tax_pdf"
        )
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "docs": self.env[report.model].browse(docids),
            "report_type": data.get("report_type") if data else "",
        }


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    def amount_text(self, amount):
        try:
            return num2words(amount, to="currency", lang="th")
        except NotImplementedError:
            return num2words(amount, to="currency", lang="en")

    def _compute_sum_type_other(self, lines, ttype):
        base_type_other = sum(
            lines.filtered(lambda l: l.wt_cert_income_type in ["6", "7", "8"]).mapped(
                ttype
            )
        )
        return base_type_other

    def _compute_desc_type_other(self, lines, ttype):
        base_type_other = lines.filtered(
            lambda l: l.wt_cert_income_type in ["6", "7", "8"]
        ).mapped(ttype)
        desc = ", ".join(base_type_other)
        return desc
