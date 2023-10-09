# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class ReportTaxReportXlsx(models.TransientModel):
    _inherit = "report.l10n_th_account_tax_report.report_tax_report_xlsx"

    def _get_tax_template(self, wb, data, objects):
        tax_template = super()._get_tax_template(wb, data, objects)
        if objects.show_operating_unit:
            tax_template.update(
                {
                    "9_z_operating_unit_id": {
                        "header": {"value": "Operating Unit"},
                        "data": {"value": self._render("operating_unit_id")},
                        "width": 30,
                    }
                }
            )
        return tax_template

    def _get_render_space(self, index, line, objects):
        render_space = super()._get_render_space(index, line, objects)
        if objects.show_operating_unit:
            render_space.update(
                {
                    "operating_unit_id": line.operating_unit_id.display_name or ""
                }
            )
        return render_space

    def _write_ws_footer(self, row_pos, ws, objects):
        row_pos = super()._write_ws_footer(row_pos, ws, objects)
        if objects.show_operating_unit:
            ws.merge_range(row_pos, 8, row_pos, 9, "")       
        return row_pos

    def _get_header_data_list(self, objects):
        header_data_list = super()._get_header_data_list(objects)
        header_data_list.append(("Operating Unit", objects.operating_unit_ids and ", ".join(objects.operating_unit_ids.mapped("display_name")) or "All"))
        return header_data_list
