# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


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

    def _update_content_currency_update(
        self, bot_currency, content, result, date_from, date_to
    ):
        data = result["data"]
        last_updated = data["data_header"]["last_updated"]
        date_last_update = datetime.datetime.strptime(last_updated, "%Y-%m-%d").date()
        if date_from > date_last_update and date_to > date_last_update:
            raise UserError(_("BOT Last Updated: {}").format(last_updated))
        data_details = data["data_detail"]
        for data_detail in data_details:
            period = (
                fields.Date.from_string(data_detail["period"]).strftime(
                    DEFAULT_SERVER_DATE_FORMAT
                )
                if data_detail["period"]
                else False
            )
            if period:
                if period in content.keys():
                    content[period][bot_currency.name] = 1.0 / float(
                        data_detail[bot_currency.bot_currency_rate_type]
                    )
                else:
                    content[period] = {
                        bot_currency.name: 1.0
                        / float(data_detail[bot_currency.bot_currency_rate_type])
                    }

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
            ICP = self.env["ir.config_parameter"].sudo()
            bot_client_id = self.company_id.bot_client_id
            if not bot_client_id:
                raise UserError(_("No bot.or.th credentials specified!"))
            hostname = ICP.get_param("hostname_TH_BOT")
            route_BOT = ICP.get_param("route_TH_BOT_exchange_daily")
            url = "{}{}/?start_period={}&end_period={}".format(
                hostname,
                route_BOT,
                date_from.strftime("%Y-%m-%d"),
                date_to.strftime("%Y-%m-%d"),
            )
            headers = {"X-IBM-Client-Id": bot_client_id, "accept": "application/json"}
            bot_currencies = self.env["res.currency"].search(
                [("name", "in", currencies)]
            )
            content = dict()
            for bot_currency in bot_currencies:
                currency = bot_currency.bot_currency_name
                url = "{}&currency={}".format(url, currency)
                response = requests.get(url, headers=headers, timeout=15)
                data_dict = response.json()
                result = data_dict.get("result", False)
                if not result:
                    raise UserError(
                        _("httpCode: %(http_code)s\nmoreInformation: %(more_info)s")
                        % (
                            {
                                "http_code": data_dict.get("httpCode", False),
                                "more_info": data_dict.get("moreInformation", False),
                            }
                        )
                    )
                self._update_content_currency_update(
                    bot_currency, content, result, date_from, date_to
                )
            return content
        return super()._obtain_rates(base_currency, currencies, date_from, date_to)
