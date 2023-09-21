# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportCurrencyUnrealizedReportXlsx(models.AbstractModel):
    _name = "report.l10n_th_revaluation.curr_unrealized_report_xlsx"
    _description = "Currency Unrealized Report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        for ws_params in self._get_ws_params(workbook, data):
            ws_name = ws_params.get("ws_name")
            ws_name = self._check_ws_name(ws_name)
            ws = workbook.add_worksheet(ws_name)
            generate_ws_method = getattr(self, ws_params["generate_ws_method"])
            generate_ws_method(workbook, ws, ws_params, data, objects)

    def _get_ws_params(self, wb, data):
        filter_template = {
            "1_report_name": {
                "header": {"value": "Report"},
                "data": {
                    "value": self._render("report_name"),
                    "format": FORMATS["format_tcell_center"],
                },
            },
            "2_company": {
                "header": {"value": "Company"},
                "data": {
                    "value": self._render("company"),
                    "format": FORMATS["format_tcell_center"],
                },
            },
            "3_company_currency": {
                "header": {"value": "Company Currency"},
                "data": {
                    "value": self._render("company_currency"),
                    "format": FORMATS["format_tcell_center"],
                },
            },
        }
        curr_unrealized_template = {
            "1_name": {
                "header": {"value": "Partner"},
                "data": {
                    "value": self._render("name"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 25,
            },
            "2_move_name": {
                "header": {"value": "Journal Entry"},
                "data": {
                    "value": self._render("move_name"),
                    "format": FORMATS["format_tcell_left"],
                },
                "width": 25,
            },
            "3_gl_foreign_balance": {
                "header": {"value": "Curr. Balance YTD"},
                "data": {"value": self._render("gl_foreign_balance")},
                "width": 25,
            },
            "4_curr_name": {
                "header": {"value": ""},
                "data": {
                    "value": self._render("curr_name"),
                    "format": FORMATS["format_tcell_center"],
                },
                "width": 5,
            },
            "5_gl_currency_rate": {
                "header": {"value": "Revaluation Rate"},
                "data": {
                    "value": self._render("gl_currency_rate"),
                    "format": FORMATS["format_tcell_right"],
                },
                "width": 25,
            },
            "6_gl_revaluated_balance": {
                "header": {"value": "Revaluated Amount YTD"},
                "data": {"value": self._render("gl_revaluated_balance")},
                "width": 25,
            },
            "7_acc_rate": {
                "header": {"value": "Accounting Rate"},
                "data": {
                    "value": self._render("acc_rate"),
                    "format": FORMATS["format_tcell_right"],
                },
                "width": 25,
            },
            "8_gl_balance": {
                "header": {"value": "Balance YTD"},
                "data": {"value": self._render("gl_balance")},
                "width": 25,
            },
            "9_gl_ytd_balance": {
                "header": {"value": "Gain(+)/Loss(-) YTD"},
                "data": {"value": self._render("gl_ytd_balance")},
                "width": 25,
            },
        }

        ws_params = {
            "ws_name": "Currency Gain and Loss",
            "generate_ws_method": "_curr_unrealized_report",
            "title": "Currency Unrealized Report",
            "wanted_list_filter": [k for k in sorted(filter_template.keys())],
            "col_specs_filter": filter_template,
            "wanted_list": [k for k in sorted(curr_unrealized_template.keys())],
            "col_specs": curr_unrealized_template,
        }
        return [ws_params]

    def _curr_unrealized_report(self, wb, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        # Title
        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)
        # Filter Table
        row_pos = self._write_filter_header(row_pos, ws, ws_params, objects)
        row_pos = self._write_filter_data(row_pos, ws, ws_params, objects)
        # Data Table
        row_pos = self._write_data_table(row_pos, ws, ws_params, objects, data)

    def _write_filter_header(self, row_pos, ws, ws_params, objects):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        return row_pos

    def _write_filter_data(self, row_pos, ws, ws_params, objects):
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={
                "report_name": "Currency Gain and Loss",
                "company": objects.company_id.name or "",
                "company_currency": objects.company_id.currency_id.name or "",
            },
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        return row_pos

    def _write_data_table(self, row_pos, ws, ws_params, objects, data):
        report_obj = self.env[
            "report.l10n_th_multicurrency_revaluation.curr_unrealized_report"
        ]
        values = report_obj._get_report_values(objects.ids, data)
        for account in values["docs"]:
            # Header
            row_pos += 1
            ws.write_string(
                row_pos,
                0,
                "{} - {}".format(account.code, account.name),
                FORMATS["format_left_bold"],
            )
            row_pos += 1
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="header",
                default_format=FORMATS["format_theader_blue_center"],
            )
            # Lines
            sh_acc = values["shell_accounts"][account.id]
            for line in sh_acc.ordered_lines:
                row_pos = self._write_line(
                    ws,
                    row_pos,
                    ws_params,
                    col_specs_section="data",
                    render_space={
                        "name": line.get("name") or "-",
                        "move_name": line.get("move_name") or "-",
                        "gl_foreign_balance": line.get("gl_foreign_balance") or 0.0,
                        "curr_name": line.get("curr_name") or "-",
                        "gl_currency_rate": line.get("gl_currency_rate")
                        and 1.0 / line.get("gl_currency_rate")
                        or 0.0,
                        "gl_revaluated_balance": line.get("gl_revaluated_balance")
                        or 0.0,
                        "acc_rate": line.get("acc_rate") or 0.0,
                        "gl_balance": line.get("gl_balance") or 0.0,
                        "gl_ytd_balance": line.get("gl_ytd_balance") or 0.0,
                    },
                    default_format=FORMATS["format_tcell_amount_right"],
                )
            # Total
            ws.write_string(row_pos, 0, "TOTAL", FORMATS["format_theader_blue_left"])
            ws.write_row(
                row_pos,
                1,
                [
                    "",
                    "",
                    "",
                    "",
                    sh_acc.gl_revaluated_balance_total or 0.0,
                    "",
                    sh_acc.gl_balance_total or 0.0,
                    sh_acc.gl_ytd_balance_total or 0.0,
                ],
                FORMATS["format_theader_blue_amount_right"],
            )
            row_pos += 1
        return row_pos
