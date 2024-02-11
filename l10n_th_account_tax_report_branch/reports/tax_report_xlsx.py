# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ReportTaxReportXlsx(models.TransientModel):
    _inherit = "report.l10n_th_account_tax_report.report_tax_report_xlsx"

    def _get_tax_template(self):
        tax_template = super()._get_tax_template()
        tax_template.update(
            {
                "6_z_company_tax_branch": {
                    "header": {"value": "Company Tax Branch"},
                    "data": {"value": self._render("company_tax_branch")},
                    "width": 20,
                },
            }
        )
        return tax_template

    def _get_render_space(self, index, line):
        render_space = super()._get_render_space(index, line)
        render_space["company_tax_branch"] = line.company_tax_branch.name or ""
        return render_space

    def _get_header_data_list(self, objects):
        data_list = super()._get_header_data_list(objects)
        # company tax branch
        data_list[4] = (
            "Company Tax Branch",
            objects._get_tax_branch_filter(objects.branch_ids) or "-",
        )
        return data_list
