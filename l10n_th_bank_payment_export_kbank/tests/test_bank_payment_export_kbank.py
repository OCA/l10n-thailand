# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import Command, fields
from odoo.exceptions import ValidationError

from odoo.addons.l10n_th_bank_payment_export.tests.common import CommonBankPaymentExport


class TestBankPaymentExportKBank(CommonBankPaymentExport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_company.allow_out_payment = False
        cls.partner_company.acc_number = "123-4-56789-0"
        cls.journal = cls.company_data["default_journal_bank"]
        cls.journal.bank_account_id = cls.partner_company
        cls.bank_ing.bic = "KASITHBK"
        cls.partner_1.write(
            {
                "name": "บริษัท ทดสอบ & จำกัด",
                "street": "12 ถนนทดสอบ",
                "street2": "แขวงทดสอบ",
                "city": "กรุงเทพ",
                "state_id": False,
                "vat": "1234567890123",
                "kbank_sms": "0812345678",
                "kbank_sms_lang": "TH",
                "kbank_advice_mode": "E",
                "kbank_email": "pay@example.com",
            }
        )
        cls.bank_bnp.write({"bank_code": "002", "bank_branch_code": False})
        cls.partner1_bank_bnp.write(
            {
                "acc_number": "987-6-54321-0",
                "acc_holder_name": "ผู้รับ & เงิน",
                "acc_holder_name_en": "Payee & Co",
            }
        )

    def _export(self, product="DCT", amounts=(100.01, 200.02)):
        same = product in ("FTR", "FTL", "DCT", "PCT")
        payments = self.env["account.payment"].create(
            [
                {
                    "payment_type": "outbound",
                    "partner_type": "supplier",
                    "partner_id": self.partner_1.id,
                    "partner_bank_id": self.partner1_bank_bnp.id,
                    "journal_id": self.journal.id,
                    "amount": amount,
                    "name": f"PAY{i + 1:06d}",
                    "memo": "ทดสอบ & <รายละเอียด>",
                }
                for i, amount in enumerate(amounts)
            ]
        )
        return self.bank_payment_export_model.create(
            {
                "name": "BATCH0001",
                "bank": "KASITHBK",
                "bank_template_id": self.env.ref(
                    "l10n_th_bank_payment_export_kbank.kbank_transfer_"
                    + ("same_bank" if same else "other_bank")
                ).id,
                "effective_date": date(2026, 9, 15),
                "kbank_charge_bearer": "N",
                "kbank_product_type" if same else "kbank_payment_type": product,
                "export_line_ids": [
                    Command.create({"payment_id": p.id}) for p in payments
                ],
            }
        )

    @staticmethod
    def _record(length, values):
        """Independent one-based positions transcribed from the bank's VBA layout."""
        result = [" "] * length
        for start, value in values:
            result[start - 1 : start - 1 + len(value)] = value
        return "".join(result)

    def _expected(self, export, product):
        same = product in ("FTR", "FTL", "DCT", "PCT")
        today = fields.Date.context_today(export).strftime("%y%m%d")
        if same:
            header = self._record(
                178,
                [
                    (1, "H" + product),
                    (5, "BATCH0001"),
                    (21, "000000"),
                    (41, "1234567890"),
                    (52, "000000000030003"),
                    (68, today),
                    (99, export.company_id.name[:50]),
                    (149, "260915"),
                    (155, "000000000000000002"),
                    (173, "N"),
                ],
            )
        else:
            header = self._record(
                82,
                [
                    (1, "H" + product),
                    (5, "1234567890"),
                    (15, "BATCH0001"),
                    (31, "15-09-2026"),
                    (46, "000000000000000002"),
                    (64, "00000000000300.03".zfill(18)),
                    (82, "N"),
                ],
            )
        result = [header]
        for idx, amount in enumerate(("100.01", "200.02"), 1):
            if same:
                detail = self._record(
                    742,
                    [
                        (1, f"D{idx:06d}"),
                        (22, "9876543210"),
                        (33, amount.replace(".", "").zfill(15)),
                        (49, today),
                        (80, "ผู้รับ & เงิน"),
                        (130, "260915"),
                        (136, "000"),
                        (139, f"PAY{idx:06d}"),
                        (205, "E"),
                        (256, "pay@example.com"),
                        (306, "0000000000.00" * 3),
                        (355, "1234567890123"),
                        (368, "12 ถนนทดสอบ"),
                        (398, "แขวงทดสอบ"),
                        (428, "กรุงเทพ"),
                        (488, "ทดสอบ & <รายละเอียด>"),
                    ],
                )
            else:
                account = (
                    "9876543210"
                    if product in ("BNL", "IPP")
                    else "00000000009876543210"
                )
                detail = self._record(
                    738,
                    [
                        (1, f"D{idx:06d}"),
                        (12, amount.zfill(13)),
                        (25, "Payee & Co" if product == "BNL" else "ผู้รับ & เงิน"),
                        (105, "12 ถนนทดสอบ"),
                        (135, "แขวงทดสอบ"),
                        (165, "กรุงเทพ"),
                        (225, account),
                        (245, f"PAY{idx:06d}"),
                        (261, "1234567890123"),
                        (274, "9999" if product == "IPP" else "987 "),
                        (278, "002"),
                        (281, "ทดสอบ & <รายละเอียด>"),
                        (596, "E"),
                        (647, "pay@example.com"),
                        (697, "0000000000.00" * 3),
                        (736, "000"),
                    ],
                )
            result.append(detail)
            if product not in ("FTR", "PCT", "PCL"):
                result.append("M" + "0812345678".ljust(54) + "TH")
        return "\r\n".join(result) + "\r\n"

    def test_all_products_match_bank_layout(self):
        for product in ("FTR", "FTL", "DCT", "PCT", "MCL", "MCS", "BNL", "PCL", "IPP"):
            with self.subTest(product=product):
                export = self._export(product)
                self.assertEqual(
                    export._generate_bank_payment_text(),
                    self._expected(export, product),
                )

    def test_download_is_ansi_without_html_escaping(self):
        export = self._export()
        self.assertEqual(export.bank_template_id.file_encoding, "cp874")
        content, kind = self.env["ir.actions.report"]._render_qweb_text(
            "l10n_th_bank_payment_export.action_payment_txt", export.ids
        )
        self.assertEqual(kind, "text")
        self.assertEqual(content, self._expected(export, "DCT").encode("cp874"))
        self.assertNotIn(b"&amp;", content)
        self.assertNotIn(b"&lt;", content)
        self.assertTrue(content.endswith(b"\r\n"))

    def test_download_uses_configured_encoding(self):
        export = self._export()
        export.bank_template_id.file_encoding = "utf-8-sig"
        content, kind = self.env["ir.actions.report"]._render_qweb_text(
            "l10n_th_bank_payment_export.action_payment_txt", export.ids
        )
        self.assertEqual(kind, "text")
        self.assertEqual(content, self._expected(export, "DCT").encode("utf-8-sig"))

    def _add_wht(self, export, count=2):
        payment = export.export_line_ids[0].payment_id
        return self.env["withholding.tax.cert"].create(
            {
                "partner_id": payment.partner_id.id,
                "payment_id": payment.id,
                "income_tax_form": "pnd53",
                "date": date(2026, 9, 9),
                "number": "WHT000001",
                "state": "done",
                "wht_line": [
                    Command.create(
                        {
                            "wht_cert_income_type": "5",
                            "wht_cert_income_desc": "ค่าบริการ",
                            "base": 1000.0,
                            "amount": 30.0,
                        }
                    )
                    for _ in range(count)
                ],
            }
        )

    def test_wht_rows_totals_and_payroll_sms(self):
        for product in ("DCT", "PCT", "FTL", "MCL", "MCS", "BNL", "PCL", "IPP"):
            with self.subTest(product=product):
                export = self._export(product, amounts=(1940.0,))
                self._add_wht(export)
                rows = export._generate_bank_payment_text().splitlines()
                self.assertEqual([r[0] for r in rows], ["H", "D", "T", "T", "M"])
                self.assertEqual(
                    rows[2],
                    "T07"
                    + "1         "
                    + "003.00"
                    + "ค่าบริการ".ljust(40)
                    + "0000001000.00"
                    + "0000000030.00"
                    + " " * 13
                    + "1",
                )
                self.assertEqual(rows[3], rows[2][:3] + "2" + rows[2][4:])
                self.assertEqual(len(rows[2]), 99)
                same = product in ("DCT", "PCT", "FTL")
                self.assertEqual(rows[1][135:138] if same else rows[1][735:738], "002")
                if product != "FTL":
                    offset = 305 if same else 696
                    self.assertEqual(
                        rows[1][offset : offset + 39],
                        "0000002000.00" + "0000000060.00" + "0000000000.00",
                    )

    def test_cancelled_wht_and_optional_sms(self):
        export = self._export()
        self._add_wht(export).state = "cancel"
        self.partner_1.kbank_sms = False
        rows = export._generate_bank_payment_text().splitlines()
        self.assertEqual([r[0] for r in rows], ["H", "D", "D"])
        self.assertEqual(rows[1][135:138], "000")

    def test_branch_and_account_rules(self):
        export = self._export("MCL", amounts=(1.0,))
        payment = export.export_line_ids.payment_id
        for code, account, product, branch in [
            ("030", "123456789012", "MCL", "9990"),
            ("030", "123456789012", "IPP", "9999"),
            ("030", "123456789012345", "BNL", "1234"),
            ("066", "123456789012", "MCS", "345 "),
            ("034", "123456789012", "PCL", "0000"),
            ("045", "12345678901", "BNL", "0010"),
            ("080", "1234567890", "BNL", "0001"),
        ]:
            with self.subTest(code=code, product=product):
                self.bank_bnp.bank_code = code
                self.partner1_bank_bnp.acc_number = account
                export.kbank_payment_type = product
                self.assertEqual(export._kbank_branch(payment), branch)
                expected = (
                    account.ljust(20)
                    if product in ("BNL", "IPP")
                    else account.zfill(20)
                )
                self.assertEqual(export._kbank_payee_account(payment), expected)
        self.bank_bnp.bank_branch_code = "0123"
        self.assertEqual(export._kbank_branch(payment), "0123")

    def test_invalid_data_does_not_mark_exported(self):
        export = self._export()
        for memo in ("bad\nrecord", "unsupported 😀"):
            with self.subTest(memo=memo):
                export.export_line_ids.payment_id.memo = memo
                with self.assertRaises(ValidationError):
                    export.action_export_text_file()
                self.assertEqual(export.state, "draft")
        export.export_line_ids.payment_id.memo = "valid"
        self.partner_1.kbank_sms_lang = False
        with self.assertRaisesRegex(ValidationError, "SMS language"):
            export._generate_bank_payment_text()

    def test_excess_wht_and_amount_are_rejected(self):
        export = self._export()
        cert = self._add_wht(export, count=4)
        with self.assertRaisesRegex(ValidationError, "at most 3"):
            export._generate_bank_payment_text()
        cert.state = "cancel"
        export.export_line_ids[0].payment_id.amount = 10000000000000.0
        with self.assertRaisesRegex(ValidationError, "allowed length"):
            export._generate_bank_payment_text()

    def test_satang_rounding(self):
        export = self._export()
        self.assertEqual(export._kbank_satang(100.015), "10002")
        self.assertEqual(export._kbank_satang(0.29), "29")
