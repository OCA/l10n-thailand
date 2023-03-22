# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class ReportNonPurchaseReportXlsx(models.AbstractModel):
    _name = "report.l10n_th_gov_purchase_report.report_non_purchase_xlsx"
    _inherit = "common.purchase.report.xlsx"
    _description = "Non Purchase Report XLSX"

    def _set_col_specs(self, ctx_format):
        return {
            "1_number": {
                "header": {
                    "value": "ลำดับที่",
                },
                "data": {
                    "value": self._render("number"),
                    "format": ctx_format["format_tcell_center"],
                },
                "width": 7,
            },
            "2_partner_vat": {
                "header": {
                    "value": "เลขประจำผู้เสียภาษี / เลขประจำตัวประชาชน",
                },
                "data": {
                    "value": self._render("partner_vat"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 30,
            },
            "3_partner": {
                "header": {
                    "value": "ชื่อผู้ประกอบการ",
                },
                "data": {
                    "value": self._render("partner"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 40,
            },
            "4_description": {
                "header": {
                    "value": "รายการพัสดุที่จัดซื้อจัดจ้าง",
                },
                "data": {
                    "value": self._render("description"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 50,
            },
            "5_total_amount": {
                "header": {
                    "value": "จำนวนเงินรวมที่จัดซื้อจัดจ้าง\n(บาท)",
                },
                "data": {
                    "value": self._render("total_amount"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 20,
            },
            "6_doc_ref_no": {
                "header": {
                    "value": "",
                },
                "data": {
                    "value": self._render("doc_ref_no"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 20,
            },
            "7_doc_ref_date": {
                "header": {
                    "value": "",
                },
                "data": {
                    "value": self._render("doc_ref_date"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 12,
            },
            "8_reason": {
                "header": {
                    "value": "เหตุผลสนับสนุน",
                },
                "data": {
                    "value": self._render("reason"),
                    "format": ctx_format["format_tcell_center"],
                },
                "width": 12,
            },
            "9_fin_no": {
                "header": {
                    "value": "เลขที่เอกสารตาม Expense",
                },
                "data": {
                    "value": self._render("fin_no"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 20,
            },
        }

    def _get_purchase_ws_name(self):
        return "Non Purchase Report"

    def _get_purchase_ws_method(self):
        return "_non_purchase_report"

    def _get_purchase_title(self):
        return "รายงานเบิกจ่ายไม่ผ่านจัดซื้อจัดจ้าง"

    def _render_space_non_procurement(self, line, i):
        return {
            "number": i,
            "partner_vat": line.bill_partner_id.vat or "",
            "partner": line.bill_partner_id.display_name or "",
            "description": line.name or "",
            "total_amount": line.total_amount or 0,
            "doc_ref_no": line.reference or "",
            "doc_ref_date": self._change_ad_to_be(line.date) or "",
            "reason": line.purchase_type_id.code or "",
            "fin_no": line.sheet_id.number or "",
        }

    def _non_purchase_report(self, workbook, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        ws.set_row(0, 22)
        ws.set_row(1, 22)
        ws.set_row(2, 22)
        ws.set_row(4, 30)
        self._set_column_width(ws, ws_params)
        # Format
        ctx_format = self._get_format(workbook)
        format_theader_blue_center = FORMATS["format_theader_blue_center"]
        format_theader_blue_center.set_align("vcenter")
        # Title
        wl = ws_params.get("wanted_list")
        title = ws_params.get("title")
        row_pos = 0
        ws.merge_range(
            row_pos, 0, row_pos, len(wl) - 1, title, ctx_format["format_ws_title"]
        )
        # Subtitle (Row 2)
        row_pos += 1
        ws.merge_range(
            row_pos,
            0,
            row_pos,
            len(wl) - 1,
            "ณ วันที่ {} - {}".format(
                self._change_ad_to_be(objects.date_from).strftime("%d/%m/%Y"),
                self._change_ad_to_be(objects.date_to).strftime("%d/%m/%Y"),
            ),
            ctx_format["format_ws_title"],
        )
        # Subtital (Row 3)
        row_pos += 1
        ws.merge_range(
            row_pos,
            0,
            row_pos,
            len(wl) - 1,
            objects.company_id.display_name,
            ctx_format["format_ws_title"],
        )
        # Column header details (Row 5)
        row_pos += 2
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=format_theader_blue_center,
        )
        # Subcolumn header details (Row 6)
        ws.merge_range("F5:G5", "เอกสารอ้างอิง", format_theader_blue_center)
        row_pos += 1
        ws.write_string("F{}".format(row_pos), "เลขที่", format_theader_blue_center)
        ws.write_string("G{}".format(row_pos), "วันที่", format_theader_blue_center)
        ws.freeze_panes(row_pos, 0)
        # Column Detail (Row 7+)
        for i, line in enumerate(objects.results):
            i += 1
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._render_space_non_procurement(line, i),
                default_format=ctx_format["format_tcell_left"],
            )
