# Preview Code System Setup Guide

## Overview
The preview code system provides early access control for OneTaskAssistant, limiting onboarding to users with valid preview codes.

## Setup Steps

### 1. Environment Variables
Make sure your `.env` file includes:
```bash
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-primary-key
COSMOS_DATABASE_NAME=1task-db
COSMOS_PREVIEW_CODES_CONTAINER_NAME=preview-codes
```

### 2. Initialize Preview Codes
Run the initialization script to create the preview codes container and insert the 25 generated codes:

```bash
python initialize_preview_codes.py
```

This script will:
- Create the `preview-codes` container in CosmosDB
- Insert all 25 generated preview codes
- Run basic validation tests
- Display usage statistics

### 3. Deploy Functions
Deploy your updated Azure Functions with the new preview code endpoints:

```bash
func azure functionapp publish your-function-app-name
```

### 4. Test the System
Test the preview code validation endpoint:

```bash
curl -X POST https://your-function-app.azurewebsites.net/api/preview-codes/validate \
  -H "Content-Type: application/json" \
  -d '{"code":"WSHA61P9","user_id":"test-user-123"}'
```

Expected response:
```json
{
  "valid": true,
  "message": "Preview code is valid",
  "error": null,
  "code_id": "WSHA61P9"
}
```

## API Endpoints

### Preview Code Validation
**POST** `/api/preview-codes/validate`

Request:
```json
{
  "code": "WSHA61P9",
  "user_id": "user-12345"
}
```

Response (Success):
```json
{
  "valid": true,
  "message": "Preview code is valid",
  "error": null,
  "code_id": "WSHA61P9"
}
```

Response (Code Already Used):
```json
{
  "valid": false,
  "message": "This preview code has already been used",
  "error": "CODE_ALREADY_USED",
  "code_id": null
}
```

Response (Invalid Code):
```json
{
  "valid": false,
  "message": "Invalid preview code. Please check your code and try again.",
  "error": "INVALID_CODE",
  "code_id": null
}
```

### Preview Code Statistics
**GET** `/api/preview-codes/stats`

Response:
```json
{
  "total_codes": 25,
  "used_codes": 8,
  "remaining_codes": 17,
  "usage_rate": 32.0,
  "recent_usage": [
    {
      "code": "WSHA61P9",
      "used_by": "user-12345",
      "used_at": "2025-09-28T15:30:00Z"
    }
  ]
}
```

## Generated Preview Codes
Here are your 25 preview codes for distribution:

1. WSHA61P9    14. GIV1SGIJ
2. F7WQUWYS    15. 8U3YEW49
3. 1PHZ5MG3    16. DEBG4CU5
4. K2TV2NU5    17. 4P2GI8WY
5. ZLQQX14D    18. N5X19GBM
6. NV9I9IVY    19. 5NGHZCGT
7. YEW4C753    20. 7PTE4AMP
8. 72SQQPNK    21. 24Q4YMG8
9. RKAFLHWJ    22. ECNLZ3NV
10. I4QDZ6WY   23. 6448ZFBK
11. BUKEF4R8   24. PU9II8NN
12. 9Z1NKGD8   25. 8TFQ95N6
13. JG7RSHA2

## Database Schema

### Preview Codes Container
- **Container Name**: `preview-codes`
- **Partition Key**: `/code`
- **Document Structure**:
```json
{
  "id": "WSHA61P9",
  "code": "WSHA61P9",
  "user_id": "system",
  "document_type": "preview_code",
  "is_used": false,
  "used_by_user_id": null,
  "used_at": null,
  "created_at": "2025-09-28T12:00:00Z",
  "updated_at": "2025-09-28T12:00:00Z"
}
```

### User Profile Updates
User profiles now include:
- `preview_code_used`: The preview code used during registration
- `contact_address`: Contact/shipping address information
- `billing_address`: Billing address information
- `billing_address_same_as_contact`: Boolean flag for address matching

## Security Features

1. **Single-use enforcement**: Each code can only be used once
2. **Backend validation**: No client-side bypass possible
3. **User tracking**: Each code usage is tied to a user ID
4. **Audit trail**: Full history of code creation and usage
5. **Error handling**: Comprehensive error responses

## Monitoring

Monitor these metrics through the stats endpoint:
- Total codes generated
- Number of codes used
- Usage rate percentage
- Recent usage activity
- Remaining available codes

## Troubleshooting

### Common Issues

1. **"Container not found" error**
   - Run `python initialize_preview_codes.py` to create containers

2. **"Code already exists" during initialization**
   - This is normal if running the script multiple times

3. **"Invalid code" for valid codes**
   - Check if the code was already used
   - Verify the code spelling (case-insensitive)

4. **Environment variable errors**
   - Ensure `.env` file is properly configured
   - Check CosmosDB connection strings

### Reset System (Development Only)
To reset all preview codes for testing:

```python
# Run in Python console (be careful!)
from preview_code_repository import preview_code_repo
from cosmos_config import cosmos_manager

# This will delete all preview codes - use with caution!
# container = cosmos_manager.get_preview_codes_container()
# for item in container.query_items("SELECT * FROM c", enable_cross_partition_query=True):
#     container.delete_item(item, partition_key=item['code'])
```

Then re-run the initialization script to recreate the codes.

## Integration with Frontend

The frontend `ProfileSetup.jsx` component automatically integrates with this system:
1. User enters preview code during profile setup
2. Code is validated in real-time via the API
3. Valid codes are marked as used upon profile creation
4. Invalid/used codes show appropriate error messages

Once a user successfully completes onboarding with a valid preview code, they have full access to the OneTaskAssistant system.
