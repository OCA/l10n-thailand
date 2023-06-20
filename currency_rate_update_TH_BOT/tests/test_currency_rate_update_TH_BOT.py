# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestResCurrencyRateProviderBOT(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.Company = self.env["res.company"]
        self.CurrencyRate = self.env["res.currency.rate"]
        self.CurrencyRateProvider = self.env["res.currency.rate.provider"]

        self.today = fields.Date.today()
        self.thb_currency = self.env.ref("base.THB")
        self.eur_currency = self.env.ref("base.EUR")
        self.my_company = self.Company.create(
            {"name": "Test Company", "currency_id": self.thb_currency.id}
        )
        self.none_provider = self.CurrencyRateProvider.create(
            {
                "service": "none",
                "currency_ids": [(4, self.eur_currency.id)],
                "company_id": self.my_company.id,
            }
        )
        self.bot_provider = self.CurrencyRateProvider.create(
            {
                "service": "BOT",
                "currency_ids": [(4, self.eur_currency.id)],
                "company_id": self.my_company.id,
            }
        )
        self.CurrencyRate.search([]).unlink()

    def test_01_supported_currencies(self):
        # None
        supported_currencies = self.none_provider._get_supported_currencies()
        self.assertNotEqual(len(supported_currencies), 48)
        # BOT
        supported_currencies = self.bot_provider._get_supported_currencies()
        self.assertEqual(len(supported_currencies), 48)

    def test_02_base_curency_not_THB(self):
        self.company1 = self.Company.create(
            {"name": "Test Company EUR", "currency_id": self.eur_currency.id}
        )
        self.bot_provider1 = self.CurrencyRateProvider.create(
            {
                "service": "BOT",
                "currency_ids": [(4, self.thb_currency.id)],
                "company_id": self.company1.id,
            }
        )
        date = self.today - relativedelta(days=1)
        self.bot_provider1._update(date, date)
        # Check service BOT
        self.assertIn(self.eur_currency, self.bot_provider1.available_currency_ids)
        self.none_provider._update(date, date)

    def test_03_update_no_clien_id(self):
        self.my_company.bot_client_id = False
        date = self.today - relativedelta(days=1)
        self.bot_provider._update(date, date)

    def test_04_update_clien_id_fail(self):
        self.my_company.bot_client_id = "Test"
        date = self.today - relativedelta(days=1)
        self.bot_provider._update(date, date)

    def test_05_update_content(self):
        """After call api to BOT, it will return value"""
        result_demo = {
            "timestamp": "2023-09-19 00:00:00",
            "api": "Daily Weighted-average Interbank Exchange Rate - THB / USD",
            "data": {
                "data_header": {
                    "report_name_eng": "Rates of Exchange of Commercial Banks in "
                    "Bangkok Metropolis (2002-present)",
                    "report_name_th": "อัตราแลกเปลี่ยนเฉลี่ยของธนาคารพาณิชย์"
                    "ในกรุงเทพมหานคร (2545-ปัจจุบัน)",
                    "report_uoq_name_eng": "(Unit: Baht / 1 Unit of Foreign Currency)",
                    "report_uoq_name_th": "(หน่วย: บาท ต่อ 1 หน่วยเงินตราต่างประเทศ)",
                    "report_source_of_data": [
                        {
                            "source_of_data_eng": "Bank of Thailand",
                            "source_of_data_th": "ธนาคารแห่งประเทศไทย",
                        }
                    ],
                    "report_remark": [
                        {
                            "report_remark_eng": "Since Nov 16, 2015 the data regarding "
                            "Buying Transfer Rate of PKR has been changed to "
                            "Buying Rate using Foreign Exchange Rates "
                            "(THOMSON REUTERS) with Bangkok Market Crossing.",
                            "report_remark_th": "ตั้งแต่วันที่ 16 พ.ย. 2558 "
                            "ข้อมูลในอัตราซื้อเงินโอนของสกุล PKR ได้เปลี่ยนเป็นอัตราซื้อ"
                            "ที่ใช้อัตราในตลาดต่างประเทศ (ทอมสันรอยเตอร์) คำนวณ"
                            "ผ่านอัตราซื้อขายเงินดอลลาร์ สรอ. ในตลาดกรุงเทพฯ",
                        }
                    ],
                    "last_updated": "2023-09-19",
                },
                "data_detail": [
                    {
                        "period": "2023-09-19",
                        "currency_id": "USD",
                        "currency_name_th": "สหรัฐอเมริกา : ดอลลาร์ (USD)",
                        "currency_name_eng": "USA : DOLLAR (USD) ",
                        "buying_sight": "35.5795000",
                        "buying_transfer": "35.6563000",
                        "selling": "35.9808000",
                        "mid_rate": "35.8186000",
                    }
                ],
            },
        }
        date = datetime.datetime.strptime("2023-09-19", "%Y-%m-%d").date()
        # Test with content there is no value
        self.bot_provider._update_content_currency_update(
            self.eur_currency, {}, result_demo, date, date
        )
        # Test with content there is value
        self.bot_provider._update_content_currency_update(
            self.eur_currency,
            {"2023-09-19": {"USD": 0.027918455774374205}},
            result_demo,
            date,
            date,
        )
        # Check not found currency when call api.
        with self.assertRaises(UserError):
            result_demo["data"]["data_header"]["last_updated"] = "2023-09-10"
            self.bot_provider._update_content_currency_update(
                self.eur_currency, {}, result_demo, date, date
            )
