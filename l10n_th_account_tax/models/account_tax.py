# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import api, fields, models
from odoo.exceptions import ValidationError

INCOME_TAX_FORM = [
    ("pnd1", "PND1"),
    ("pnd2", "PND2"),
    ("pnd3", "PND3"),
    ("pnd3a", "PND3a"),
    ("pnd53", "PND53"),
]


WHT_CERT_INCOME_TYPE = [
    ("1", "1. เงินเดือน ค่าจ้าง ฯลฯ 40(1)"),
    ("2", "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)"),
    ("3", "3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3)"),
    ("4A", "4. ดอกเบี้ย ฯลฯ 40(4)ก"),
    (
        "4B11",
        (
            "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.1) "
            "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ 30 ของกำไรสุทธิ"
        ),
    ),
    (
        "4B12",
        (
            "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.2) "
            "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ 25 ของกำไรสุทธิ"
        ),
    ),
    (
        "4B13",
        (
            "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.3) "
            "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ 20 ของกำไรสุทธิ"
        ),
    ),
    (
        "4B14",
        (
            "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (1.4) "
            "กิจการที่ต้องเสียภาษีเงินได้นิติบุคคลร้อยละ อื่นๆ (ระบุ) ของกำไรสุทธิ"
        ),
    ),
    (
        "4B21",
        (
            "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.1) "
            "กำไรสุทธิกิจการที่ได้รับยกเว้นภาษีเงินได้นิติบุคคล"
        ),
    ),
    (
        "4B22",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.2) ได้รับยกเว้นไม่ต้องนำมารวมคำนวณเป็นรายได้",
    ),
    (
        "4B23",
        (
            "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.3) "
            "กำไรสุทธิส่วนที่หักผลขาดทุนสุทธิยกมาไม่เกิน 5 ปี"
        ),
    ),
    (
        "4B24",
        "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.4) กำไรที่รับรู้ทางบัญชีโดยวิธีส่วนได้เสีย",
    ),
    ("4B25", "4. เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข (2.5) อื่นๆ (ระบุ)"),
    ("5", "5. ค่าจ้างทำของ ค่าบริการ ค่าเช่า ค่าขนส่ง ฯลฯ 3 เตรส"),
    ("6", "6. อื่นๆ (ระบุ)"),
]


# PND tax tags per income tax form, on the base or tax repartition lines
INCOME_TAX_FORM_TAGS = {
    "pnd53": ("l10n_th.tag_th_pnd53", "l10n_th.tag_th_income_pnd53"),
    "pnd3": ("l10n_th.tag_th_pnd3", "l10n_th.tag_th_income_pnd3"),
    "pnd3a": (
        "l10n_th_account_tax.tag_th_pnd3a",
        "l10n_th_account_tax.tag_th_income_pnd3a",
    ),
    "pnd2": (
        "l10n_th_account_tax.tag_th_pnd2",
        "l10n_th_account_tax.tag_th_income_pnd2",
    ),
    "pnd1": (
        "l10n_th_account_tax.tag_th_pnd1",
        "l10n_th_account_tax.tag_th_income_pnd1",
    ),
}

# Rows of the withholding tax certificate per standard income tax type,
# as on the standard 50 Tawi report. Dividends need a sub-row of 4(b).
L10N_TH_INCOME_TAX_TYPE_CERT_INCOME_TYPE = {
    "service": "2",
    "commission": "2",
    "royalties": "3",
    "interest": "4A",
    "rentals": "5",
    "prof_fees": "5",
    "contract": "5",
    "transportation": "5",
    "advertising": "5",
    "insurance": "5",
    "public_actor": "5",
    "prize": "5",
    "hire_of_work": "5",
    "others": "6",
}


class AccountTax(models.Model):
    _inherit = "account.tax"

    is_pit = fields.Boolean(
        string="Personal Income Tax",
        help="Withholding amount is computed on payment from the PIT rate table, "
        "based on the yearly accumulated income of the partner",
    )
    taxinv_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Tax Invoice Sequence",
        help="Optional sequence as Tax Invoice number",
        copy=False,
    )
    sequence_number_next = fields.Integer(
        string="Next Number",
        help="The next sequence number will be used for the next tax invoice.",
        compute="_compute_seq_number_next",
        inverse="_inverse_seq_number_next",
    )

    @api.onchange("is_pit")
    def _onchange_is_pit(self):
        if self.is_pit:
            self.amount_type = "percent"
            self.amount = 0.0

    @api.constrains(
        "is_pit",
        "is_withholding_tax",
        "type_tax_use",
        "amount_type",
        "amount",
        "country_id",
    )
    def _check_is_pit(self):
        for tax in self.filtered("is_pit"):
            if tax.country_code != "TH":
                raise ValidationError(
                    self.env._(
                        "Personal income tax %(tax)s must be a Thai tax.",
                        tax=tax.display_name,
                    )
                )
            if not tax.is_withholding_tax or tax.type_tax_use != "purchase":
                raise ValidationError(
                    self.env._(
                        "Personal income tax %(tax)s must be "
                        "a purchase withholding tax.",
                        tax=tax.display_name,
                    )
                )
            if tax.amount_type != "percent" or tax.amount:
                raise ValidationError(
                    self.env._(
                        "Personal income tax %(tax)s must be a percentage tax of 0%%, "
                        "its amount is computed from the PIT rate table.",
                        tax=tax.display_name,
                    )
                )
            if self.search_count(
                [
                    ("is_pit", "=", True),
                    ("company_id", "=", tax.company_id.id),
                    ("id", "!=", tax.id),
                ]
            ):
                raise ValidationError(
                    self.env._("Only one personal income tax is allowed per company.")
                )

    def _get_wht_cert_income_tax_form(self, partner):
        """Income tax form of the withholding tax certificate, from the PND tax
        tags of the tax as the standard 50 Tawi report, else from the partner"""
        self.ensure_one()
        tags = self.repartition_line_ids.tag_ids
        for form, xmlids in INCOME_TAX_FORM_TAGS.items():
            for xmlid in xmlids:
                if self.env.ref(xmlid, raise_if_not_found=False) in tags:
                    return form
        return "pnd53" if partner.commercial_partner_id.is_company else "pnd3"

    def _get_wht_cert_income_type(self):
        """Type of income of the withholding tax certificate,
        from the standard income tax type"""
        self.ensure_one()
        return L10N_TH_INCOME_TAX_TYPE_CERT_INCOME_TYPE.get(
            self.l10n_th_income_tax_type, False
        )

    @api.depends(
        "taxinv_sequence_id.use_date_range", "taxinv_sequence_id.number_next_actual"
    )
    def _compute_seq_number_next(self):
        for tax in self:
            tax.sequence_number_next = 1
            if tax.taxinv_sequence_id:
                sequence = tax.taxinv_sequence_id._get_current_sequence()
                tax.sequence_number_next = sequence.number_next_actual

    def _inverse_seq_number_next(self):
        for tax in self:
            if tax.taxinv_sequence_id and tax.sequence_number_next:
                sequence = tax.taxinv_sequence_id._get_current_sequence()
                sequence.sudo().number_next = tax.sequence_number_next

    @api.model
    def _prepare_base_line_tax_repartition_grouping_key(
        self, base_line, base_line_grouping_key, tax_data, tax_rep_data
    ):
        grouping_key = super()._prepare_base_line_tax_repartition_grouping_key(
            base_line, base_line_grouping_key, tax_data, tax_rep_data
        )

        # Keep 0% VAT lines for tax invoices, but not zero withholding tax
        record = base_line.get("record")
        if (
            isinstance(record, models.BaseModel)
            and "company_id" in record
            and record.company_id.tax_zero_line
            and not tax_data["tax"].is_withholding_tax
        ):
            grouping_key["__keep_zero_line"] = True

        return grouping_key
