# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCalendarPublicHolidaySync(TransactionCase):
    """Test calendar public holiday BOT API synchronization"""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.holiday_model = self.env["calendar.public.holiday"]
        self.holiday_line_model = self.env["calendar.public.holiday.line"]
        # Create a public holiday record
        self.public_holiday = self.holiday_model.create(
            {
                "year": 2024,
                "country_id": self.env.ref("base.th").id,
            }
        )

    def test_get_api_config_valid(self):
        """Test _get_api_config with valid configuration"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = "test-client-id"
        config = self.public_holiday._get_api_config()
        self.assertEqual(config["route_path"], "https://api.example.com/v1/holidays/")
        self.assertEqual(config["client_id"], "test-client-id")
        self.assertEqual(config["year"], "2024")

    def test_get_api_config_missing_route_path(self):
        """Test _get_api_config raises error when route_path is missing"""
        self.company.route_path = False
        self.company.api_client_id = "test-client-id"
        with self.assertRaises(ValidationError) as context:
            self.public_holiday._get_api_config()
        self.assertIn("Route path and API Client ID", str(context.exception))

    def test_get_api_config_missing_client_id(self):
        """Test _get_api_config raises error when api_client_id is missing"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = False
        with self.assertRaises(ValidationError) as context:
            self.public_holiday._get_api_config()
        self.assertIn("Route path and API Client ID", str(context.exception))

    @patch("requests.get")
    def test_call_bot_api_success(self, mock_get):
        """Test _call_api_public_holiday with successful response"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = "test-client-id"
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": {"data": []}}
        mock_get.return_value = mock_response
        config = self.public_holiday._get_api_config()
        response = self.public_holiday._call_api_public_holiday(config)
        self.assertEqual(response.json(), {"result": {"data": []}})
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_call_bot_api_timeout(self, mock_get):
        """Test _call_api_public_holiday handles connection timeout"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = "test-client-id"
        mock_get.side_effect = requests.Timeout("Connection timeout")
        config = self.public_holiday._get_api_config()
        with self.assertRaises(ValidationError) as context:
            self.public_holiday._call_api_public_holiday(config)
        self.assertIn("Connection timeout", str(context.exception))

    @patch("requests.get")
    def test_call_bot_api_connection_error(self, mock_get):
        """Test _call_api_public_holiday handles connection error"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = "test-client-id"
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        config = self.public_holiday._get_api_config()
        with self.assertRaises(ValidationError) as context:
            self.public_holiday._call_api_public_holiday(config)
        self.assertIn("Connection error", str(context.exception))

    @patch("requests.get")
    def test_call_bot_api_http_error(self, mock_get):
        """Test _call_api_public_holiday handles HTTP error"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = "test-client-id"
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        config = self.public_holiday._get_api_config()
        with self.assertRaises(ValidationError) as context:
            self.public_holiday._call_api_public_holiday(config)
        self.assertIn("HTTP error", str(context.exception))

    def test_parse_bot_response_valid_json(self):
        """Test _parse_bot_response with valid JSON"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "data": [
                    {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"},
                    {"Date": "2024-02-14", "HolidayDescriptionThai": "วันวาเลนไทน์"},
                ]
            }
        }
        holidays = self.public_holiday._parse_bot_response(mock_response)
        self.assertEqual(len(holidays), 2)
        self.assertEqual(holidays[0]["Date"], "2024-01-01")
        self.assertEqual(holidays[0]["HolidayDescriptionThai"], "วันขึ้นปีใหม่")

    def test_parse_bot_response_invalid_json(self):
        """Test _parse_bot_response with invalid JSON"""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        with self.assertRaises(ValidationError) as context:
            self.public_holiday._parse_bot_response(mock_response)
        self.assertIn("Invalid JSON response", str(context.exception))

    def test_normalize_bot_response_with_result_key(self):
        """Test _normalize_bot_response with result key"""
        json_res = {
            "result": {
                "data": [{"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"}]
            }
        }
        holidays = self.public_holiday._normalize_bot_response(json_res)
        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0]["Date"], "2024-01-01")

    def test_normalize_bot_response_list_format(self):
        """Test _normalize_bot_response with list format"""
        json_res = [
            {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"},
            {"Date": "2024-02-14", "HolidayDescriptionThai": "วันวาเลนไทน์"},
        ]
        holidays = self.public_holiday._normalize_bot_response(json_res)
        self.assertEqual(len(holidays), 2)

    def test_normalize_bot_response_single_dict(self):
        """Test _normalize_bot_response with single dict format"""
        json_res = {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"}
        holidays = self.public_holiday._normalize_bot_response(json_res)
        self.assertEqual(len(holidays), 1)
        self.assertEqual(holidays[0]["Date"], "2024-01-01")

    def test_prepare_bot_holiday_lines_valid(self):
        """Test _prepare_bot_holiday_lines with valid data"""
        result = {
            "result": {
                "data": [
                    {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"},
                    {"Date": "2024-02-14", "HolidayDescriptionThai": "วันวาเลนไทน์"},
                ]
            }
        }
        holidays = self.public_holiday._prepare_bot_holiday_lines(result)
        self.assertEqual(len(holidays), 2)
        self.assertEqual(holidays[0]["Date"], "2024-01-01")
        self.assertEqual(holidays[0]["HolidayDescriptionThai"], "วันขึ้นปีใหม่")

    def test_prepare_bot_holiday_lines_missing_fields(self):
        """Test _prepare_bot_holiday_lines filters items with missing fields"""
        result = {
            "result": {
                "data": [
                    {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"},
                    {"Date": "2024-02-14"},  # Missing HolidayDescriptionThai
                    {"HolidayDescriptionThai": "วันวาเลนไทน์"},  # Missing Date
                ]
            }
        }

        holidays = self.public_holiday._prepare_bot_holiday_lines(result)
        self.assertEqual(len(holidays), 1)

    def test_prepare_bot_holiday_lines_invalid_result(self):
        """Test _prepare_bot_holiday_lines with invalid result"""
        holidays = self.public_holiday._prepare_bot_holiday_lines(None)
        self.assertEqual(holidays, [])
        holidays = self.public_holiday._prepare_bot_holiday_lines("invalid")
        self.assertEqual(holidays, [])

    def test_sync_bot_holiday_lines_create_new(self):
        """Test _sync_bot_holiday_lines creates new holiday lines"""
        holidays = [
            {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"},
            {"Date": "2024-02-14", "HolidayDescriptionThai": "วันวาเลนไทน์"},
        ]
        result = self.public_holiday._sync_bot_holiday_lines(holidays)
        self.assertEqual(result["created"], 2)
        self.assertEqual(result["updated"], 0)
        lines = self.holiday_line_model.search(
            [("public_holiday_id", "=", self.public_holiday.id)]
        )
        self.assertEqual(len(lines), 2)

    def test_sync_bot_holiday_lines_update_existing(self):
        """Test _sync_bot_holiday_lines updates existing holiday lines"""
        # Create an existing holiday line
        existing_line = self.holiday_line_model.create(
            {
                "name": "Old Name",
                "date": "2024-01-01",
                "public_holiday_id": self.public_holiday.id,
                "variable_date": False,
            }
        )
        holidays = [
            {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่ - Updated"},
        ]
        result = self.public_holiday._sync_bot_holiday_lines(holidays)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 1)
        # Reload the record to get updated values
        updated_line = self.holiday_line_model.browse(existing_line.id)
        self.assertEqual(updated_line.name, "วันขึ้นปีใหม่ - Updated")

    def test_sync_bot_holiday_lines_wrong_year(self):
        """Test _sync_bot_holiday_lines filters holidays from wrong year"""
        holidays = [
            {"Date": "2025-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่ 2025"},
        ]
        result = self.public_holiday._sync_bot_holiday_lines(holidays)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 0)

    def test_sync_bot_holiday_lines_missing_fields(self):
        """Test _sync_bot_holiday_lines skips items with missing fields"""
        holidays = [
            {"Date": "2024-01-01"},  # Missing name
            {"HolidayDescriptionThai": "วันขึ้นปีใหม่"},  # Missing date
        ]
        result = self.public_holiday._sync_bot_holiday_lines(holidays)
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 0)

    @patch("requests.get")
    def test_action_sync_bot_holidays_full_flow(self, mock_get):
        """Test full action_sync_bot_holidays flow"""
        self.company.route_path = "https://api.example.com/v1/holidays/"
        self.company.api_client_id = "test-client-id"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "data": [
                    {"Date": "2024-01-01", "HolidayDescriptionThai": "วันขึ้นปีใหม่"},
                    {"Date": "2024-02-14", "HolidayDescriptionThai": "วันวาเลนไทน์"},
                ]
            }
        }
        mock_get.return_value = mock_response
        result = self.public_holiday.action_sync_bot_holidays()
        self.assertTrue(result)
        lines = self.holiday_line_model.search(
            [("public_holiday_id", "=", self.public_holiday.id)]
        )
        self.assertEqual(len(lines), 2)

    def test_country_default_thailand(self):
        """Test default country is Thailand"""
        # The default country should be Thailand (set in the model)
        self.assertEqual(self.public_holiday.country_id, self.env.ref("base.th"))
