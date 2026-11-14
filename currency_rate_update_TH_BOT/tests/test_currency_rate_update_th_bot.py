# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from unittest import mock

import requests
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestResCurrencyRateProviderBOT(BaseCommon):
    _test_user_groups = ("base.group_system", "base.group_partner_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Company = cls.env["res.company"]
        cls.CurrencyRate = cls.env["res.currency.rate"]
        cls.CurrencyRateProvider = cls.env["res.currency.rate.provider"]

        cls.today = fields.Date.today()
        cls.thb_currency = cls.env.ref("base.THB")
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.eur_currency.active = True
        cls.my_company = cls.Company.create(
            {"name": "Test Company", "currency_id": cls.thb_currency.id}
        )
        cls._test_user.company_ids += cls.my_company
        cls.none_provider = cls.CurrencyRateProvider.create(
            {
                "service": "none",
                "currency_ids": [(4, cls.eur_currency.id)],
                "company_id": cls.my_company.id,
            }
        )
        cls.bot_provider = cls.CurrencyRateProvider.create(
            {
                "service": "BOT",
                "currency_ids": [(4, cls.eur_currency.id)],
                "company_id": cls.my_company.id,
            }
        )
        cls.CurrencyRate.search([]).unlink()

    @classmethod
    def _get_bot_response(cls, data, status_code=200):
        response = mock.Mock()
        response.status_code = status_code
        response.json.return_value = data
        return response

    @classmethod
    def _get_bot_data(cls, details, last_updated="2023-09-19"):
        """Response of BOT, details: list of (period, currency, name, mid_rate)"""
        return {
            "result": {
                "data": {
                    "data_header": {"last_updated": last_updated},
                    "data_detail": [
                        {
                            "period": period,
                            "currency_id": currency,
                            "currency_name_eng": name,
                            "mid_rate": mid_rate,
                        }
                        for period, currency, name, mid_rate in details
                    ],
                }
            }
        }

    def test_01_supported_currencies(self):
        # None
        supported_currencies = self.none_provider._get_supported_currencies()
        self.assertNotEqual(len(supported_currencies), 48)
        # BOT
        supported_currencies = self.bot_provider._get_supported_currencies()
        self.assertEqual(len(supported_currencies), 48)

    @mute_logger("odoo.addons.currency_rate_update.models.res_currency_rate_provider")
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

    @mute_logger("odoo.addons.currency_rate_update.models.res_currency_rate_provider")
    def test_03_update_no_clien_id(self):
        self.my_company.bot_token = False
        date = self.today - relativedelta(days=1)
        self.bot_provider._update(date, date)

    @mute_logger("odoo.addons.currency_rate_update.models.res_currency_rate_provider")
    def test_04_update_clien_id_fail(self):
        self.my_company.bot_token = "Test"
        date = self.today - relativedelta(days=1)
        response = self._get_bot_response(
            {"httpCode": "401", "moreInformation": "Invalid Credentials"}
        )
        with mock.patch.object(requests, "get", return_value=response):
            self.bot_provider._update(date, date)
        self.assertFalse(
            self.CurrencyRate.search([("company_id", "=", self.my_company.id)])
        )

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
                            "report_remark_eng": "Since Nov 16, 2015 the data regarding"
                            " Buying Transfer Rate of PKR has been changed to "
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
        date = datetime.date(2023, 9, 19)
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

    def test_06_obtain_rates(self):
        """After call api to BOT, rate is normalized to 1 unit of currency"""
        self.my_company.bot_token = "Test"
        jpy_currency = self.env.ref("base.JPY")
        jpy_currency.active = True
        result_demo = {
            "result": {
                "data": {
                    "data_header": {"last_updated": "2023-09-19"},
                    "data_detail": [
                        {
                            "period": "2023-09-19",
                            "currency_id": "JPY",
                            "mid_rate": "24.2000000",
                        },
                        # Data without period is skipped
                        {
                            "period": "",
                            "currency_id": "JPY",
                            "mid_rate": "0.0000000",
                        },
                    ],
                }
            }
        }
        response = mock.Mock()
        response.json.return_value = result_demo
        date = datetime.date(2023, 9, 19)
        with mock.patch.object(requests, "get", return_value=response):
            content = self.bot_provider._obtain_rates("THB", ["JPY"], date, date)
        # BOT quotes JPY per 100 units
        self.assertEqual(content, {"2023-09-19": {"JPY": 100.0 / 24.2}})
        # Check error returned by BOT is raised to the user.
        response.json.return_value = {
            "httpCode": "401",
            "moreInformation": "Missing Credentials",
        }
        with (
            mock.patch.object(requests, "get", return_value=response),
            self.assertRaises(UserError),
        ):
            self.bot_provider._obtain_rates("THB", ["JPY"], date, date)

    def test_07_bot_currency_name(self):
        """BOT currency name follows the currency name by default"""
        self.eur_currency.name = "EUX"
        self.assertEqual(self.eur_currency.bot_currency_name, "EUX")

    def test_08_obtain_rates_one_request(self):
        """Rates of all currencies are obtained in one request"""
        self.my_company.bot_token = "Test"
        currencies = self.env["res.currency"]
        for xmlid in ("base.USD", "base.JPY", "base.IDR"):
            currency = self.env.ref(xmlid)
            currency.active = True
            currencies += currency
        response = self._get_bot_response(
            self._get_bot_data(
                [
                    ("2023-09-19", "USD", "USA : DOLLAR (USD) ", "35.8186000"),
                    ("2023-09-19", "JPY", "JAPAN : YEN (100 YEN) (JPY)", "24.2000000"),
                    (
                        "2023-09-19",
                        "IDR",
                        "INDONESIA : RUPIAH (1,000 RUPIAH) (IDR)",
                        "2.3300000",
                    ),
                    # Currency not requested and rate not available are skipped
                    ("2023-09-19", "EUR", "EURO ZONE : EURO (EUR)", "38.2000000"),
                    ("2023-09-18", "USD", "USA : DOLLAR (USD) ", ""),
                ]
            )
        )
        date = datetime.date(2023, 9, 19)
        with mock.patch.object(requests, "get", return_value=response) as mock_get:
            content = self.bot_provider._obtain_rates(
                "THB", currencies.mapped("name"), date, date
            )
        mock_get.assert_called_once()
        self.assertNotIn("currency=", mock_get.call_args.args[0])
        self.assertEqual(
            content,
            {
                "2023-09-19": {
                    "USD": 1.0 / 35.8186,
                    "JPY": 100.0 / 24.2,
                    "IDR": 1000.0 / 2.33,
                }
            },
        )

    def test_09_obtain_rates_split_period(self):
        """BOT limits the period of a request to 31 days"""
        self.my_company.bot_token = "Test"
        response = self._get_bot_response(
            self._get_bot_data(
                [("2023-09-19", "EUR", "EURO ZONE : EURO (EUR)", "38.2000000")]
            )
        )
        date_from = datetime.date(2023, 8, 1)
        date_to = datetime.date(2023, 9, 19)
        with mock.patch.object(requests, "get", return_value=response) as mock_get:
            content = self.bot_provider._obtain_rates(
                "THB", ["EUR"], date_from, date_to
            )
        self.assertEqual(
            [call.args[0].split("?")[1] for call in mock_get.call_args_list],
            [
                "start_period=2023-08-01&end_period=2023-08-31",
                "start_period=2023-09-01&end_period=2023-09-19",
            ],
        )
        self.assertEqual(content, {"2023-09-19": {"EUR": 1.0 / 38.2}})

    def test_10_update_share_request(self):
        """Providers of many companies share the requests to BOT"""
        self.my_company.bot_token = "Test"
        company2 = self.Company.create(
            {
                "name": "Test Company 2",
                "currency_id": self.thb_currency.id,
                "bot_token": "Test2",
            }
        )
        bot_provider2 = self.CurrencyRateProvider.create(
            {
                "service": "BOT",
                "currency_ids": [(4, self.eur_currency.id)],
                "company_id": company2.id,
            }
        )
        response = self._get_bot_response(
            self._get_bot_data(
                [("2023-09-19", "EUR", "EURO ZONE : EURO (EUR)", "38.2000000")]
            )
        )
        date = datetime.date(2023, 9, 19)
        with mock.patch.object(requests, "get", return_value=response) as mock_get:
            (self.bot_provider + bot_provider2)._update(date, date)
        mock_get.assert_called_once()
        rates = self.CurrencyRate.search(
            [("currency_id", "=", self.eur_currency.id), ("name", "=", date)]
        )
        self.assertEqual(rates.company_id, self.my_company + company2)
        for rate in rates:
            self.assertAlmostEqual(rate.inverse_company_rate, 38.2)

    def test_11_obtain_rates_no_data(self):
        """Currency without data on BOT does not block other currencies"""
        self.my_company.bot_token = "Test"
        date = datetime.date(2023, 9, 19)
        response = self._get_bot_response({"result": {"data": None}})
        with mock.patch.object(requests, "get", return_value=response):
            content = self.bot_provider._obtain_rates("THB", ["EUR"], date, date)
        self.assertEqual(content, {})
        # Limit of requests to BOT is reached
        response = self._get_bot_response({}, status_code=429)
        with (
            mock.patch.object(requests, "get", return_value=response),
            self.assertRaises(UserError),
        ):
            self.bot_provider._obtain_rates("THB", ["EUR"], date, date)
        # Response is not a json
        response = self._get_bot_response({}, status_code=502)
        response.json.side_effect = ValueError()
        with (
            mock.patch.object(requests, "get", return_value=response),
            self.assertRaises(UserError),
        ):
            self.bot_provider._obtain_rates("THB", ["EUR"], date, date)
