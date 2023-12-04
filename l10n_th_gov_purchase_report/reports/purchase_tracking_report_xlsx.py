# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models

from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION
from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class ReportPurchaseTrackingReportXlsx(models.AbstractModel):
    _name = "report.l10n_th_gov_purchase_report.report_po_tracking_xlsx"
    _inherit = "common.purchase.report.xlsx"
    _description = "Purchase Tracking Report XLSX"

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
            "02_pr_name": {
                "header": {
                    "value": "เลขที่ขอซื้อขอจ้าง/PR",
                },
                "data": {
                    "value": self._render("pr_name"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "03_pr_requested_by": {
                "header": {
                    "value": "ผู้ขอซื้อขอจ้าง",
                },
                "data": {
                    "value": self._render("pr_requested_by"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 20,
            },
            "04_pr_description": {
                "header": {
                    "value": "รายการที่ขอจัดซื้อจัดจ้าง",
                },
                "data": {
                    "value": self._render("pr_description"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 40,
            },
            "05_pr_procurement_type": {
                "header": {
                    "value": "ประเภทการซื้อหรือจ้าง",
                },
                "data": {
                    "value": self._render("pr_procurement_type"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "06_pr_procurement_method": {
                "header": {
                    "value": "วิธีการจัดซื้อหรือจ้าง",
                },
                "data": {
                    "value": self._render("pr_procurement_method"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 12,
            },
            "07_pr_total_cost": {
                "header": {
                    "value": "วงเงินงบประมาณที่ขอซื้อหรือจ้าง (บาท)",
                },
                "data": {
                    "value": self._render("pr_total_cost"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 25,
            },
            "08_pr_date_start": {
                "header": {
                    "value": "วันที่ขอซื้อขอจ้าง/PR",
                },
                "data": {
                    "value": self._render("pr_date_start"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 15,
            },
            "09_te_number": {
                "header": {
                    "value": "เลขที่เอกสารการเสนอราคา/TE",
                },
                "data": {
                    "value": self._render("te_number"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 20,
            },
            "10_rfq_number": {
                "header": {
                    "value": "เลขที่ใบเสนอราคา/RFQ",
                },
                "data": {
                    "value": self._render("rfq_number"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "11_rfq_deadline": {
                "header": {
                    "value": "วันที่ใบเสนอราคา/RFQ",
                },
                "data": {
                    "value": self._render("rfq_deadline"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 15,
            },
            "12_po_number": {
                "header": {
                    "value": "เลขที่สัญญา/PO",
                },
                "data": {
                    "value": self._render("po_number"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 12,
            },
            "13_po_date_start": {
                "header": {
                    "value": "วันที่เริ่มต้นสัญญา (PO/Agreement)",
                },
                "data": {
                    "value": self._render("po_date_start"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 20,
            },
            "14_po_date_end": {
                "header": {
                    "value": "วันที่สิ้นสุดสัญญา (PO/Agreement)",
                },
                "data": {
                    "value": self._render("po_date_end"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 20,
            },
            "15_po_vendor": {
                "header": {
                    "value": "ชื่อผู้รับจ้าง/ผู้ขาย (PO/Agreement)",
                },
                "data": {
                    "value": self._render("po_vendor"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 25,
            },
            "16_po_toal": {
                "header": {
                    "value": "วงเงินที่ตกลงทำสัญญา/PO",
                },
                "data": {
                    "value": self._render("po_total"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 18,
            },
            "17_invoice_plan_total": {
                "header": {
                    "value": "จำนวนงวดทั้งหมด",
                },
                "data": {
                    "value": self._render("invoice_plan_total"),
                    "format": ctx_format["format_tcell_center"],
                },
                "width": 12,
            },
            "18_invoice_plan_count": {
                "header": {
                    "value": "งวดที่ส่งงาน",
                },
                "data": {
                    "value": self._render("invoice_plan_count"),
                    "format": ctx_format["format_tcell_center"],
                },
                "width": 12,
            },
            "19_invoice_plan_amount": {
                "header": {
                    "value": "เงินงวดตามสัญญา",
                },
                "data": {
                    "value": self._render("invoice_plan_amount"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 12,
            },
            "20_wa_number": {
                "header": {
                    "value": "เลขที่ใบตรวจรับ/WA",
                },
                "data": {
                    "value": self._render("wa_number"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "21_wa_date": {
                "header": {
                    "value": "วันที่ใบตรวจรับ/WA",
                },
                "data": {
                    "value": self._render("wa_date"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 15,
            },
            "22_wa_responsible": {
                "header": {
                    "value": "ชื่อเจ้าหน้าที่พัสดุที่ได้รับมอบหมายจัดซื้อจัดจ้าง",
                },
                "data": {
                    "value": self._render("wa_responsible"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 30,
            },
            "23_move_number": {
                "header": {
                    "value": "เลขที่ Vendor Bill",
                },
                "data": {
                    "value": self._render("move_number"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 15,
            },
            "24_move_date": {
                "header": {
                    "value": "วันที่ Vendor Bill",
                },
                "data": {
                    "value": self._render("move_date"),
                    "format": ctx_format["format_tcell_date_right"],
                },
                "width": 15,
            },
            "25_move_amount": {
                "header": {
                    "value": "จำนวนเงินที่เบิกจ่าย",
                },
                "data": {
                    "value": self._render("move_amount"),
                    "format": ctx_format["format_tcell_amount_right"],
                },
                "width": 15,
            },
            "26_payment_state": {
                "header": {
                    "value": "สถานะการจ่ายเงิน / Payment Status",
                },
                "data": {
                    "value": self._render("payment_state"),
                    "format": ctx_format["format_tcell_left"],
                },
                "width": 30,
            },
        }

    def _get_purchase_ws_name(self):
        return "Purchase Tracking Report"

    def _get_purchase_ws_method(self):
        return "_purchase_tracking_report"

    def _get_purchase_title(self):
        return "รายงานการติดตามสถานะการจัดซื้อจัดจ้าง"

    def _render_space_purchase_tracking_report(self, duplicate, line, i):
        line = line.sudo()
        pr = line.pr_id
        te = line.te_id
        po = line.po_id
        agm = line.agm_id
        wa = line.wa_id
        move = line.move_id
        if duplicate:
            pr = self.env["purchase.request"]
            i = ""
        rfq_number = po.name if po.state == "draft" else po.rfq_number
        payment_state_dict = dict(PAYMENT_STATE_SELECTION)
        invoice_plan = po.invoice_plan_ids.filtered(
            lambda l: l.invoice_type == "installment"
        )
        # Check multi currency
        estimated_cost = pr.estimated_cost
        if pr.currency_id != pr.company_id.currency_id:
            estimated_cost = pr.currency_id._convert(
                estimated_cost,
                pr.company_id.currency_id,
                pr.company_id,
                pr.date_approved,
            )
        po_total_company_currency = po.amount_total
        if po.currency_id != po.company_id.currency_id:
            po_total_company_currency = po.currency_id._convert(
                po_total_company_currency,
                po.company_id.currency_id,
                po.company_id,
                po.date_approve,
            )
        return {
            "number": i,
            "pr_name": pr.name or "",
            "pr_requested_by": pr.requested_by.name or "",
            "pr_description": pr.description or "",
            "pr_procurement_type": pr.procurement_type_id.name or "",
            "pr_procurement_method": pr.procurement_method_id.name or "",
            "pr_total_cost": estimated_cost or "",
            "pr_date_start": pr.date_start or "",
            "te_number": te.name or "",
            "rfq_number": rfq_number or "",
            "rfq_deadline": po.date_order or "",
            "po_number": agm.code or po.name or "",
            "po_date_start": agm.start_date or po.date_order or "",
            "po_date_end": agm.end_date or po.date_order or "",
            "po_vendor": po.partner_id.name or "",
            "po_total": po_total_company_currency or "",
            "invoice_plan_total": len(invoice_plan) or "",
            "invoice_plan_count": wa.installment_id.installment or "",
            "invoice_plan_amount": wa.installment_id.amount or "",
            "wa_number": wa.name or "",
            "wa_date": wa.date_accept or "",
            "wa_responsible": wa.responsible_id.name or "",
            "move_number": move.name or "",
            "move_date": move.date or "",
            "move_amount": move.amount_total or "",
            "payment_state": payment_state_dict.get(move.payment_state)
            if move.payment_state
            else "",
        }

    def _purchase_tracking_report(self, workbook, ws, ws_params, data, objects):
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
        title = ws_params.get("title")
        row_pos = 0
        ws.merge_range(row_pos, 0, row_pos, 5, title, ctx_format["format_ws_title"])
        # Subtitle (Row 2)
        row_pos += 1
        ws.merge_range(
            row_pos,
            0,
            row_pos,
            5,
            "ณ วันที่ {} - {}".format(
                objects.date_from.strftime("%d/%m/%Y"),
                objects.date_to.strftime("%d/%m/%Y"),
            ),
            ctx_format["format_ws_title"],
        )
        # Subtital (Row 3)
        row_pos += 1
        ws.merge_range(
            row_pos,
            0,
            row_pos,
            5,
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
        ws.freeze_panes(row_pos, 0)
        # Column Detail
        previous_id = False
        i = 0
        for line in objects.results:
            # skip it if line duplicate
            duplicate = 0
            if previous_id == line["pr_id"]:
                duplicate = 1
            else:
                i += 1
            previous_id = line["pr_id"]
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space=self._render_space_purchase_tracking_report(
                    duplicate, line, i
                ),
                default_format=ctx_format["format_tcell_left"],
            )
