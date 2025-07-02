# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ThaiUtils(models.AbstractModel):
    _name = "thai.utils"
    _description = "Thai Localization Utilities"

    @api.model
    def to_thai_number(self, value):
        """Convert Arabic numerals to Thai numerals (0-9)."""
        str_value = str(value)
        thai_digits = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
        return str_value.translate(thai_digits)

    @api.model
    def to_arabic_number(self, value):
        """Convert Thai numerals to Arabic numerals (0-9)."""
        str_value = str(value)
        arabic_digits = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
        return str_value.translate(arabic_digits)

    @api.model
    def thai_month_name(self, month, short=False):
        """Convert month number (1-12) to Thai month name."""
        months = [
            None,
            "มกราคม",
            "กุมภาพันธ์",
            "มีนาคม",
            "เมษายน",
            "พฤษภาคม",
            "มิถุนายน",
            "กรกฎาคม",
            "สิงหาคม",
            "กันยายน",
            "ตุลาคม",
            "พฤศจิกายน",
            "ธันวาคม",
        ]
        months_abbr = [
            None,
            "ม.ค.",
            "ก.พ.",
            "มี.ค.",
            "เม.ย.",
            "พ.ค.",
            "มิ.ย.",
            "ก.ค.",
            "ส.ค.",
            "ก.ย.",
            "ต.ค.",
            "พ.ย.",
            "ธ.ค.",
        ]
        return months_abbr[month] if short else months[month]

    @api.model
    def format_thai_date(
        self, date_obj, month_format="full", buddhist_year=True, format_date=None
    ):
        """
        Format a date object to Thai date string.

        Args:
            date_obj: date object
            month_format:
                "full"    → มกราคม
                "short"   → ม.ค.
                "numeric" → 01, 02, 03
            buddhist_year (bool): use พ.ศ. or ค.ศ.
            format_date (str): format custom
        """
        day = date_obj.day

        # Month format
        if month_format == "numeric":
            month = f"{date_obj.month:02d}"
        elif month_format == "short":
            month = self.thai_month_name(date_obj.month, short=True)
        else:  # full
            month = self.thai_month_name(date_obj.month, short=False)

        # Year Format
        year = date_obj.year + 543 if buddhist_year else date_obj.year

        # Format Date
        if format_date is None:
            format_date = "{day} {month} {year}"
        return format_date.format(day=day, month=month, year=year)
