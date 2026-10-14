This module provides a utility model `thai.utils` for Thai localization features such as number and date formatting.
You can either call the methods directly via the environment, or inherit the abstract model in your own modules.

# Example

```python
thai_utils = self.env["thai.utils"]

# Convert Arabic to Thai numerals
thai_number = thai_utils.to_thai_number("1234567890")  # → ๑๒๓๔๕๖๗๘๙๐

# Convert Thai to Arabic numerals
arabic_number = thai_utils.to_arabic_number("๐๘๙")  # → 089

# Get Thai full month name
month_name = thai_utils.thai_month_name(12)  # → ธันวาคม

# Get Thai abbreviated month name
month_abbr = thai_utils.thai_month_name(12, short=True)  # → ธ.ค.

# Format date to Thai date string
from datetime import date

formatted_date = thai_utils.format_thai_date(date(2025, 7, 2))  # → 2 กรกฎาคม 2568

formatted_date_short_month = thai_utils.format_thai_date(date(2025, 7, 2), month_format="short")  # → 2 ก.ค. 2568

formatted_date_numeric_month = thai_utils.format_thai_date(date(2025, 7, 2), month_format="numeric", format_date="{day:02d}{month}{year}")  # → 02072568

formatted_year_thai = thai_utils.format_thai_date(date(2025, 7, 2), format_date="{year}")  # → 2568

```