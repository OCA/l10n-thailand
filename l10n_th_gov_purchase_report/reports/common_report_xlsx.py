# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from dateutil.relativedelta import relativedelta

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


class CommonPurchaseReportXlsx(models.AbstractModel):
    _name = "common.purchase.report.xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Common Function Purchase Report"

    def _change_ad_to_be(self, date):
        return date + relativedelta(years=543)

    def _get_format(self, wb):
        ctx_format = {
            "format_tcell_date_right": wb.add_format(
                {
                    "border": True,
                    "border_color": "#D3D3D3",
                    "num_format": "DD/MM/YYYY",
                    "align": "right",
                }
            ),
            "format_ws_title": wb.add_format(
                {"bold": True, "font_size": 14, "align": "center"}
            ),
            "format_tcell_center": FORMATS["format_tcell_center"],
            "format_tcell_left": FORMATS["format_tcell_left"],
            "format_tcell_right": FORMATS["format_tcell_right"],
            "format_tcell_amount_right": FORMATS["format_tcell_amount_right"],
        }
        for f in ctx_format:
            ctx_format[f].set_align("top")
        return ctx_format

    def _get_purchase_ws_name(self):
        return ""

    def _get_purchase_ws_method(self):
        return ""

    def _get_purchase_title(self):
        return ""

    def _get_ws_params(self, wb, data, objects):
        # Format
        ctx_format = self._get_format(wb)
        # Set col specs
        col_specs = self._set_col_specs(ctx_format)
        ws_params = {
            "ws_name": self._get_purchase_ws_name(),
            "generate_ws_method": self._get_purchase_ws_method(),
            "title": self._get_purchase_title(),
            "wanted_list": [k for k in sorted(col_specs.keys())],
            "col_specs": col_specs,
        }
        return [ws_params]

    def _set_column_hight(self, ws, ws_params):
        """
        Set hight for all columns included in the 'wanted_list'.
        """
        ws_params.get("col_specs")
        wl = ws_params.get("wanted_list") or []
        for pos in range(len(wl)):
            ws.set_row(pos, 22)
