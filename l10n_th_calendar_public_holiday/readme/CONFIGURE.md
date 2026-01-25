To use the automatic BOT API synchronization feature, follow these steps:

1. Go to **Settings > Companies > Companies** and select your company
2. Navigate to the **Public Holiday** section
3. Configure the following fields:

   - **Route Path**: The full URL to the BOT API endpoint
   - **API Client ID**: Your API key/client ID for authentication

4. Save the configuration

## Example Configuration

```
Route Path: https://gateway.api.bot.or.th/financial-institutions-holidays/
API Client ID: your-api-key-here
```

## API Requirements

The BOT API endpoint must support the following:

- **Method**: GET
- **Parameters**: `year` (required, format: YYYY)
- **Headers**:
  - `Accept: application/json`
  - `Authorization: [your-api-client-id]`
- **Response Format**:
```json
{
  "result": {
    "api": "API_V2.FIHolidays",
    "timestamp": "2026-01-25 20:29:16",
    "data": [
      {
        "HolidayWeekDay": "Thursday",
        "HolidayWeekDayThai": "วันพฤหัสบดี",
        "Date": "2026-01-01",
        "DateThai": "01/01/2569",
        "HolidayDescription": "New Year’s Day",
        "HolidayDescriptionThai": "วันขึ้นปีใหม่"
      }
    ]
  }
}
```
