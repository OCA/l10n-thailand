# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import timedelta

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

# The BOT API rejects requests on a period longer than this
BOT_MAX_PERIOD_DAYS = 31
# Fallback when the unit is not found in the currency name sent by BOT
BOT_CURRENCY_UNIT = {"JPY": 100.0, "IDR": 1000.0}
# i.e. "JAPAN : YEN (100 YEN) (JPY)", "INDONESIA : RUPIAH (1,000 RUPIAH) (IDR)"
BOT_CURRENCY_UNIT_PATTERN = re.compile(r"\(([\d,]+)\s+[^)]+\)")


class ResCurrencyRateProviderBOT(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("BOT", "Bank of Thailand")],
        ondelete={"BOT": "set default"},
    )

    @api.depends("service")
    def _compute_available_currency_ids(self):
        res = super()._compute_available_currency_ids()
        Currency = self.env["res.currency"]
        for provider in self:
            if provider.service == "BOT":
                provider.available_currency_ids = Currency.search(
                    [("bot_currency_name", "in", provider._get_supported_currencies())]
                )
        return res

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
            "CAD",
            "SEK",
            "DKK",
            "NOK",
            "CNY",
            "MXN",
            "ZAR",
            "KRW",
            "TWD",
            "KWD",
            "SAR",
            "AED",
            "MMK",
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
            "PKR",
        ]

    @api.model
    def _scheduled_update(self):
        # Share the BOT responses among the providers (companies) of this run
        return super(
            ResCurrencyRateProviderBOT, self._with_bot_rates_cache()
        )._scheduled_update()

    def _update(self, date_from, date_to, newest_only=False):
        return super(ResCurrencyRateProviderBOT, self._with_bot_rates_cache())._update(
            date_from, date_to, newest_only=newest_only
        )

    def _with_bot_rates_cache(self):
        """BOT rates are the same for every company, and BOT limits the number
        of requests per hour: keep the responses to request each period once."""
        if "bot_rates_cache" in self.env.context:
            return self
        return self.with_context(bot_rates_cache={})

    def _get_currency_unit(self, bot_currency_name, bot_currency_description=None):
        """
        Returns the currency unit used to normalize the exchange rate to 1 unit.

        For example, if the exchange rate is provided as 100 JPY, this method returns
        100.0, so that the rate can be converted to a per-1 JPY basis.
        The unit is read from the currency name sent by BOT, i.e.
        "JAPAN : YEN (100 YEN) (JPY)".
        """
        match = BOT_CURRENCY_UNIT_PATTERN.search(bot_currency_description or "")
        if match:
            return float(match.group(1).replace(",", ""))
        return BOT_CURRENCY_UNIT.get(bot_currency_name, 1.0)

    def _update_content_currency_update(
        self, bot_currency, content, result, date_from, date_to
    ):
        data = result.get("data")
        if not data:
            # BOT has no data on this period
            return
        last_updated = data["data_header"]["last_updated"]
        date_last_update = fields.Date.to_date(last_updated)
        if date_from > date_last_update and date_to > date_last_update:
            raise UserError(self.env._("BOT Last Updated: %(date)s", date=last_updated))
        bot_currency_name = bot_currency.bot_currency_name
        for data_detail in data["data_detail"]:
            # The response has all currencies when it was not requested for one
            if data_detail.get("currency_id", bot_currency_name) != bot_currency_name:
                continue
            if not data_detail["period"]:
                continue
            try:
                bot_rate = float(data_detail[bot_currency.bot_currency_rate_type])
            except (TypeError, ValueError):
                bot_rate = 0.0
            if not bot_rate:
                continue
            period = fields.Date.to_date(data_detail["period"]).strftime(
                DEFAULT_SERVER_DATE_FORMAT
            )
            unit = self._get_currency_unit(
                bot_currency_name, data_detail.get("currency_name_eng")
            )
            content.setdefault(period, {})[bot_currency.name] = unit / bot_rate

    def _get_bot_periods(self, date_from, date_to):
        """Split the period, as BOT limits the period of a request"""
        periods = []
        while date_from <= date_to:
            period_to = min(
                date_from + timedelta(days=BOT_MAX_PERIOD_DAYS - 1), date_to
            )
            periods.append((date_from, period_to))
            date_from = period_to + timedelta(days=1)
        return periods

    def _get_bot_result(self, date_from, date_to):
        """Request the rates of all currencies on the period, in one request"""
        self.ensure_one()
        bot_token = self.company_id.bot_token
        if not bot_token:
            raise UserError(self.env._("No bot.or.th credentials specified!"))
        cache = self.env.context.get("bot_rates_cache", {})
        if (date_from, date_to) in cache:
            return cache[(date_from, date_to)]
        ICP = self.env["ir.config_parameter"].sudo()
        url = "{}{}/?start_period={}&end_period={}".format(
            ICP.get_str("hostname_TH_BOT"),
            ICP.get_str("route_TH_BOT_exchange_daily"),
            date_from.strftime("%Y-%m-%d"),
            date_to.strftime("%Y-%m-%d"),
        )
        headers = {
            "Authorization": bot_token,
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            raise UserError(
                self.env._(
                    "The limit of requests to bot.or.th is reached, "
                    "please try again later."
                )
            )
        try:
            data_dict = response.json()
        except ValueError as e:
            raise UserError(
                self.env._(
                    "Invalid response from bot.or.th (httpCode: %(http_code)s)",
                    http_code=response.status_code,
                )
            ) from e
        result = data_dict.get("result", False)
        if not result:
            raise UserError(
                self.env._(
                    "httpCode: %(http_code)s\nmoreInformation: %(more_information)s",
                    http_code=data_dict.get("httpCode", False),
                    more_information=data_dict.get("moreInformation", False),
                )
            )
        cache[(date_from, date_to)] = result
        return result

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service == "BOT":
            if base_currency != "THB":
                raise UserError(
                    self.env._(
                        "Bank of Thailand is suitable only for companies with THB as "
                        "base currency!"
                    )
                )
            bot_currencies = self.env["res.currency"].search(
                [("name", "in", currencies)]
            )
            content = {}
            for period_from, period_to in self._get_bot_periods(date_from, date_to):
                result = self._get_bot_result(period_from, period_to)
                for bot_currency in bot_currencies:
                    self._update_content_currency_update(
                        bot_currency, content, result, date_from, date_to
                    )
            return content
        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
