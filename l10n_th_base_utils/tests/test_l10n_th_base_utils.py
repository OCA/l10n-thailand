# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import datetime

from odoo.tests.common import TransactionCase


class TestThaiBaseUtils(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thai_util_model = cls.env["thai.utils"]

    def test_01_convert_thai_number(self):
        value_arabic = "459/132 ถนนสุขสวัสดิ์ แขวงราษฎร์บูรณะ เขตราษฎร์บูรณะ กรุงเทพฯ 10140"
        value_thai = "๔๕๙/๑๓๒ ถนนสุขสวัสดิ์ แขวงราษฎร์บูรณะ เขตราษฎร์บูรณะ กรุงเทพฯ ๑๐๑๔๐"

        # Convert Arabic to Thai
        self.assertEqual(self.thai_util_model.to_thai_number(value_arabic), value_thai)

        # Convert Thai to Arabic
        self.assertEqual(
            self.thai_util_model.to_arabic_number(value_thai), value_arabic
        )

    def test_02_format_thai_date(self):
        d = datetime.date(2025, 7, 2)
        result = self.thai_util_model.format_thai_date(d)
        self.assertEqual(result, "2 กรกฎาคม 2568")

        result_short = self.thai_util_model.format_thai_date(d, month_format="short")
        self.assertEqual(result_short, "2 ก.ค. 2568")

        result_numeric = self.thai_util_model.format_thai_date(
            d, month_format="numeric"
        )
        self.assertEqual(result_numeric, "2 07 2568")

        result_day_numeric = self.thai_util_model.format_thai_date(
            d, month_format="numeric", format_date="{day:02d}{month}{year}"
        )
        self.assertEqual(result_day_numeric, "02072568")

        result_year = self.thai_util_model.format_thai_date(d, format_date="{year}")
        self.assertEqual(result_year, "2568")
