# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import requests

from odoo import fields, models
from odoo.exceptions import ValidationError


class ResourceCalendarPublicHoliday(models.Model):
    _inherit = "calendar.public.holiday"

    country_id = fields.Many2one(
        default=lambda self: self.env.ref("base.th"),
    )

    def action_sync_bot_holidays(self):
        """Sync public holidays from BOT API using configured credentials."""
        self.ensure_one()
        api_data = self._get_api_config()
        response = self._call_api_public_holiday(api_data)
        holidays = self._parse_bot_response(response)
        if holidays:
            self._sync_bot_holiday_lines(holidays)
        return True

    def _get_api_config(self):
        """Get API configuration from company settings."""
        client_id = self.env.company.api_client_id
        route_path = self.env.company.route_path
        if not route_path or not client_id:
            raise ValidationError(
                self.env._(
                    "Route path and API Client ID must be configured "
                    "in company settings."
                )
            )
        return {
            "route_path": route_path,
            "client_id": client_id,
            "year": str(self.year),
        }

    def _call_api_public_holiday(self, api_data):
        params = {"year": api_data["year"]}
        headers = {
            "Accept": "application/json",
            "X-IBM-Client-Id": api_data["client_id"],
        }

        try:
            res = requests.get(
                api_data["route_path"], params=params, headers=headers, timeout=30
            )
            res.raise_for_status()
        except requests.Timeout as e:
            raise ValidationError(self.env._("Connection timeout: %s") % e) from e
        except requests.ConnectionError as e:
            raise ValidationError(self.env._("Connection error: %s") % e) from e
        except requests.HTTPError as e:
            raise ValidationError(self.env._("HTTP error: %s") % e) from e

        return res

    def _parse_bot_response(self, response):
        """Parse and normalize JSON response from BOT API."""
        try:
            json_res = response.json()
        except ValueError as e:
            raise ValidationError(
                self.env._("Invalid JSON response from API: %s") % e
            ) from e

        return self._normalize_bot_response(json_res)

    def _normalize_bot_response(self, json_res):
        """Normalize BOT API response to standard format."""
        # Ensure response is a dict with 'result' key
        if isinstance(json_res, dict) and "result" in json_res:
            result = json_res
        elif isinstance(json_res, list):
            result = {"result": {"data": json_res}}
        else:
            result = {"result": {"data": [json_res]}}

        return self._prepare_bot_holiday_lines(result)

    def _prepare_bot_holiday_lines(self, result):
        """
        Convert BOT API result to holiday line dicts
        usable by _sync_bot_holiday_lines.
        """
        if not isinstance(result, dict):
            return []

        result_data = result.get("result", {})
        holidays = result_data.get("data", [])

        if not isinstance(holidays, list):
            return []

        normalized = []
        for item in holidays:
            date = item.get("Date")
            name = item.get("HolidayDescriptionThai")

            if not date or not name:
                continue

            normalized.append(
                {
                    "Date": date,
                    "HolidayDescriptionThai": name,
                }
            )

        return normalized

    def _sync_bot_holiday_lines(self, holidays):
        """Create or update holiday lines from normalized holiday data."""
        HolidayLine = self.env["calendar.public.holiday.line"]
        created = 0
        updated = 0

        for item in holidays:
            date_str = item.get("Date")
            name = item.get("HolidayDescriptionThai")

            if not date_str or not name:
                continue

            date = fields.Date.from_string(date_str)

            if date.year != self.year:
                continue

            existing_line = HolidayLine.search(
                [
                    ("date", "=", date),
                    ("public_holiday_id", "=", self.id),
                    ("state_ids", "=", False),
                ],
                limit=1,
            )

            if existing_line:
                existing_line.write({"name": name, "variable_date": False})
                updated += 1
            else:
                HolidayLine.create(
                    {
                        "name": name,
                        "date": date,
                        "public_holiday_id": self.id,
                        "variable_date": False,
                    }
                )
                created += 1

        return {"created": created, "updated": updated}
