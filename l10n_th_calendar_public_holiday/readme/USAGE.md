## Manual Holiday Entry

You can manually add public holidays:

1. Go to **Employees > Public Holidays**
2. Create a new public holiday record
3. Set the year and add holiday dates using the line items
4. Mark the country as Thailand (default)
5. Save the record

## Automatic Synchronization from BOT API

To sync holidays automatically from the BOT API:

1. Ensure your company configuration is complete (see CONFIGURE.md section)
2. Create or select a public holiday record for the desired year
3. Click the **Sync BOT Holidays** action button
4. The system will fetch all public holidays for that year from the BOT API
5. Holidays will be automatically created or updated

## Error Handling

The module implements comprehensive error handling:

- **Connection Timeout**: Raises ValidationError with timeout message
- **Connection Error**: Raises ValidationError with connection error details
- **HTTP Error**: Raises ValidationError with HTTP status information
- **Invalid JSON**: Raises ValidationError when API response is not valid JSON
- **Missing Configuration**: Raises ValidationError when Route Path or API Client ID is not configured

## Methods

### action_sync_bot_holidays()
Main method to trigger synchronization with BOT API

### _get_api_config()
Retrieves and validates API configuration from company settings

### _call_bot_api(api_data)
Makes HTTP GET request to BOT API with proper headers and parameters

### _parse_bot_response(response)
Parses JSON response from the API

### _normalize_bot_response(json_res)
Normalizes different API response formats into standard format

### _prepare_bot_holiday_lines(result)
Extracts and filters holiday data from API response

### _sync_bot_holiday_lines(holidays)
Creates or updates holiday line records in the database
