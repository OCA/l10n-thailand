To use the automatic BOT API synchronization feature, follow these steps:

1. Go to **Settings > Companies > Companies** and select your company
2. Navigate to the **Public Holiday** section
3. Configure the following fields:

   - **Route Path**: The full URL to the BOT API endpoint
   - **API Client ID**: Your API key/client ID for authentication

4. Save the configuration

## Example Configuration

```
Route Path: https://api.example.com/v1/public-holidays/
API Client ID: your-api-key-here
```

## API Requirements

The BOT API endpoint must support the following:

- **Method**: GET
- **Parameters**: `year` (required, format: YYYY)
- **Headers**:
  - `Accept: application/json`
  - `X-IBM-Client-Id: [your-api-client-id]`
- **Response Format**:
```json
{
    "result": {
        "data": [
            {
                "Date": "2024-01-01",
                "HolidayDescriptionThai": "วันขึ้นปีใหม่"
            }
        ]
    }
}
```
