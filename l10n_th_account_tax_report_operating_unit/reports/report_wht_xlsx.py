# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class WithholdingTaxReportXslx(models.AbstractModel):
    _inherit = "report.withholding.tax.report.xlsx"

    def _get_withholding_tax_template(self, wb, data, obj):
        withholding_tax_template = super()._get_withholding_tax_template(wb, data, obj)
        if obj.show_operating_unit:
            withholding_tax_template.update(
                {
                    "99_operating_unit_id": {
                        "header": {"value": "Operating Unit"},
                        "data": {"value": self._render("operating_unit_id")},
                        "width": 30,
                    }
                }
            )
        return withholding_tax_template

    def _get_render_space(self, index, line, obj):
        render_space = super()._get_render_space(index, line, obj)
        if obj.show_operating_unit:
            render_space.update(
                {
                    "operating_unit_id": line.cert_id.operating_unit_id.display_name or ""
                }
            )
        return render_space
    
    def _write_ws_footer(self, row_pos, ws, obj):
        row_pos = super()._write_ws_footer(row_pos, ws, obj)
        if obj.show_operating_unit:
            ws.merge_range(row_pos, 9, row_pos, 11, "")
        return row_pos
    
    def _get_header_data_list(self, obj):
        header_data_list = super()._get_header_data_list(obj)
        header_data_list.append(("Operating Unit", obj.operating_unit_ids and ", ".join(obj.operating_unit_ids.mapped("display_name")) or "All"))
        return header_data_list
