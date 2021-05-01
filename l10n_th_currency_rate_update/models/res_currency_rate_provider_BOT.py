# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import http.client
import json

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ResCurrencyRateProviderBOT(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("BOT", "Bank of Thailand")],
        ondelete={"BOT": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "BOT":
            return super()._get_supported_currencies()

        # List of currencies obrained from:
        # https://apigw1.bot.or.th/bot/public/Stat-ExchangeRate/v2
        return [
            "USD",
            "GBP",
            "EUR",
            "JPY",
            "HKD",
            "MYR",
            "SGD",
            "BND",
            "PHP",
            "IDR",
            "INR",
            "CHF",
            "AUD",
            "NZD",
            "PKR",
            "CAD",
            "SEK",
            "DKK",
            "NOK",
            "CNY",
            "MXN",
            "ZAR",
            "MMK",
            "KRW",
            "TWD",
            "KWD",
            "SAR",
            "AED",
            "BDT",
            "CZK",
            "KHR",
            "KES",
            "LAK",
            "RUB",
            "VND",
            "EGP",
            "PLN",
            "LKR",
            "IQD",
            "BHD",
            "OMR",
            "JOD",
            "QAR",
            "MVR",
            "NPR",
            "PGK",
            "ILS",
            "HUF",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service == "BOT":
            if base_currency != "THB":
                raise UserError(
                    _(
                        "Bank of Thailand is suitable only for companies with THB as "
                        "base currency!"
                    )
                )
            bot_client_id = self.company_id.bot_client_id
            if not bot_client_id:
                raise UserError(_("No bot.or.th credentials specified!"))
            conn = http.client.HTTPSConnection("apigw1.bot.or.th")
            headers = {"x-ibm-client-id": bot_client_id, "accept": "application/json"}
            url = (
                "/bot/public/Stat-ExchangeRate/v2/DAILY_AVG_EXG_RATE/"
                "?start_period={}&end_period={}"
            ).format(date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))
            conn.request("GET", url, headers=headers)
            res = conn.getresponse()
            data = res.read()
            data = data.decode("utf-8")
            data_dict = data if isinstance(data, dict) else json.loads(data)
            result = data_dict.get("result", False)
            if not result:
                raise UserError(
                    _("httpCode: {}\nmoreInformation: {}").format(
                        data_dict.get("httpCode", False),
                        data_dict.get("moreInformation", False),
                    )
                )
            data_details = result["data"]["data_detail"]
            content = dict()
            for data_detail in data_details:
                period = (
                    fields.Date.from_string(data_detail["period"]).strftime(
                        DEFAULT_SERVER_DATE_FORMAT
                    )
                    if data_detail["period"]
                    else False
                )
                currency = data_detail["currency_id"]
                if period and currency in currencies:
                    if period in content.keys():
                        content[period][currency] = 1.0 / float(data_detail["mid_rate"])
                    else:
                        content[period] = {
                            currency: 1.0 / float(data_detail["mid_rate"])
                        }
            return content
        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
