# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class ReportPurchaseReportXlsx(models.AbstractModel):
    _name = "report.l10n_th_gov_purchase_report.report_purchase_xlsx"
    _inherit = "common.purchase.report.xlsx"
    _description = "Purchase Report XLSX"

    def _set_col_specs(self, ctx_format):
        return {
            "01_number": {
                "header": {
                    "value": "ลำดับที่",
                },
                "data": {
                    "value": self._render("number"),
                    "format": ctx_format["format_tcell_center"],
                },
                "width": 7,
            },
            "02_project_name": {
                "header": {
                    "value": "ชื่อโครงการ",
                },
                "data": {
                    "value": self._render("project_name"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 40,
            },
            "03_date_signed": {
                "header": {
                    "value": "วันที่ลงนามในสัญญา",
                },
                "data": {
                    "value": self._render("date_signed"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 15,
            },
            "04_pr_amount": {
                "header": {
                    "value": "วงเงินงบประมาณ (บาท)",
                },
                "data": {
                    "value": self._render("pr_amount"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 15,
            },
            # "05_market_price": {
            #     "header": {
            #         "value": "ราคากลาง (บาท)",
            #     },
            #     "data": {
            #         "value": self._render("date_signed"),
            #         "format": ctx_format["format_tcell_amount_right"],
            #     },
            #     "width": 15,
            # },
            "06_procurement_method": {
                "header": {
                    "value": "วิธีซื้อหรือจ้าง",
                },
                "data": {
                    "value": self._render("procurement_method"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "07_vendor_offer": {
                "header": {
                    "value": "",
                },
                "data": {
                    "value": self._render("vendor_offer"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 20,
            },
            "08_price_offer": {
                "header": {
                    "value": "",
                },
                "data": {
                    "value": self._render("price_offer"),
                    "format": ctx_format["format_tcell_right"],
                },
                "width": 15,
            },
            "09_vendor_name": {
                "header": {
                    "value": "",
                },
                "data": {
                    "value": self._render("vendor_name"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 20,
            },
            "10_amount_total": {
                "header": {
                    "value": "",
                },
                "data": {
                    "value": self._render("amount_total"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 15,
            },
            # "11_reason": {
            #     "header": {
            #         "value": "เหตุผลที่คัดเลือกโดยสรุป",
            #     },
            #     "data": {
            #         "value": self._render("reason"),
            #         "format": ctx_format["format_tcell_left"],
            #     },
            #     "width": 15,
            # },
            "11_po": {
                "header": {
                    "value": "เลขที่ใบสั่งซื้อสั่งจ้าง",
                },
                "data": {
                    "value": self._render("po_name"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "12_agreement": {
                "header": {
                    "value": "เลขที่สัญญา",
                },
                "data": {
                    "value": self._render("agreement_name"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
        }

    def _get_purchase_ws_name(self):
        return "Purchase Report"

    def _get_purchase_ws_method(self):
        return "_purchase_report"

    def _get_purchase_title(self):
        return "สรุปผลการดำเนินการจัดซื้อจัดจ้าง"

    def _render_space_procurement(self, line, i):
        list_vendor = []
        list_price = []
        for po in (line.requisition_id.purchase_ids).sorted("amount_total"):
            list_vendor.append(po.partner_id.name)
            list_price.append("{:,.2f}".format(po.amount_total))
        vendor_offer = ", \n".join(list_vendor)
        price_offer = ", \n".join(list_price)
        return {
            "number": i,
            "project_name": line.description or "",
            "date_signed": line.date_signed or "",
            "pr_amount": line.pr_amount or "",
            "procurement_method": line.procurement_method or "",
            "vendor_offer": vendor_offer,
            "price_offer": price_offer,
            "vendor_name": line.purchase_order_id.partner_id.name,
            "amount_total": line.purchase_order_id.amount_total,
            # "reason": line.purchase_order_id.reason or "",
            "agreement_name": line.agreement_name or "",
            "po_name": line.po_name or "",
        }

    def _purchase_report(self, workbook, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        self._set_column_hight(ws, ws_params)
        ws.set_row(4, 30)
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
        # ws.merge_range(
        #     "G5:H5", "รายชื่อผู้เสนอราคาและวงเงินที่เสนอ", format_theader_blue_center
        # )
        # ws.merge_range(
        #     "I5:J5",
        #     "ผู้ได้รับการคัดเลือกและราคาที่ตกลงซื้อหรือจ้าง",
        #     format_theader_blue_center,
        # )
        # row_pos += 1
        # ws.write_string(
        #     "G{}".format(row_pos), "ชื่อผู้เสนอราคา", format_theader_blue_center
        # )
        # ws.write_string(
        #     "H{}".format(row_pos), "ราคาที่เสนอ (บาท)", format_theader_blue_center
        # )
        # ws.write_string(
        #     "I{}".format(row_pos), "ผู้ได้รับคัดเลือก", format_theader_blue_center
        # )
        # ws.write_string(
        #     "J{}".format(row_pos), "จำนวนเงิน (บาท)", format_theader_blue_center
        # )
        ws.merge_range(
            "F5:G5", "รายชื่อผู้เสนอราคาและวงเงินที่เสนอ", format_theader_blue_center
        )
        ws.merge_range(
            "H5:I5",
            "ผู้ได้รับการคัดเลือกและราคาที่ตกลงซื้อหรือจ้าง",
            format_theader_blue_center,
        )
        row_pos += 1
        ws.write_string(
            "F{}".format(row_pos), "ชื่อผู้เสนอราคา", format_theader_blue_center
        )
        ws.write_string(
            "G{}".format(row_pos), "ราคาที่เสนอ (บาท)", format_theader_blue_center
        )
        ws.write_string(
            "H{}".format(row_pos), "ผู้ได้รับคัดเลือก", format_theader_blue_center
        )
        ws.write_string(
            "I{}".format(row_pos), "จำนวนเงิน (บาท)", format_theader_blue_center
        )

        ws.freeze_panes(row_pos, 0)
        # Column Detail
        for i, line in enumerate(objects.results):
            i += 1
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._render_space_procurement(line, i),
                default_format=ctx_format["format_tcell_left"],
            )
