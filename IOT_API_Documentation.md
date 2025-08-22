# IoT CNC Data API Documentation

This document describes the external APIs available for retrieving CNC data from the IoT Management module.

## Base URL

All API endpoints are relative to your Frappe site URL:
```
http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.
```

## Authentication

These APIs are configured with `allow_guest=True`, so no authentication is required. However, you can still use standard Frappe authentication if needed.

## Endpoints

### 1. Get CNC Data (with pagination and filtering)

**Endpoint:** `get_iot_cnc_data`

**Method:** GET or POST

**Description:** Retrieves CNC data records with optional filtering by equipment ID and pagination support.

**Parameters:**
- `equipment_id` (string, optional): Filter results by specific equipment ID
- `limit` (integer, optional): Number of records to return (default: 50, max: 1000)
- `offset` (integer, optional): Number of records to skip for pagination (default: 0)

**Example Request:**
```bash
# Get all CNC data (first 50 records)
curl "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_cnc_data"

# Get CNC data for specific equipment
curl "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_cnc_data?equipment_id=cnc-dw-16-0009"

# Get CNC data with pagination
curl "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_cnc_data?limit=100&offset=50"
```

**Response Format:**
```json
{
  "message": {
    "success": true,
    "data": [
      {
        "id": "cnc-CNC001-0001",
        "equipment_id": "CNC001",
        "workpiece_count": 150,
        "runtime": "08:30:00",
        "cutting_time": "06:45:30",
        "cnc_model": "DMG MORI NLX2500",
        "current_tool_no": "T0101",
        "operation_mode": "AUTO",
        "run_mode": "CONTINUOUS",
        "rapid_override": "100%",
        "spindle_actual_rpm": "2500",
        "feed_actual_rate": "1200",
        "spindle_load": "75%",
        "x_axis_load": "45%",
        "y_axis_load": "30%",
        "z_axis_load": "60%",
        "alarm_code": null,
        "alarm_message": null,
        "created_at": "2025-01-21 10:30:00",
        "updated_at": "2025-01-21 14:15:00"
      }
    ],
    "total_count": 1250,
    "returned_count": 1,
    "offset": 0,
    "limit": 50,
    "message": "Successfully retrieved 1 CNC data records"
  }
}
```

### 2. Get CNC Data by ID

**Endpoint:** `get_iot_cnc_data_by_id`

**Method:** GET or POST

**Description:** Retrieves a specific CNC data record by its ID.

**Parameters:**
- `cnc_data_id` (string, required): The ID of the CNC data record

**Example Request:**
```bash
curl "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_cnc_data_by_id?cnc_data_id=cnc-CNC001-0001"
```

**Response Format:**
```json
{
  "message": {
    "success": true,
    "data": {
      "id": "cnc-CNC001-0001",
      "equipment_id": "CNC001",
      "workpiece_count": 150,
      "runtime": "08:30:00",
      "cutting_time": "06:45:30",
      "cnc_model": "DMG MORI NLX2500",
      "current_tool_no": "T0101",
      "operation_mode": "AUTO",
      "run_mode": "CONTINUOUS",
      "rapid_override": "100%",
      "spindle_actual_rpm": "2500",
      "feed_actual_rate": "1200",
      "spindle_load": "75%",
      "x_axis_load": "45%",
      "y_axis_load": "30%",
      "z_axis_load": "60%",
      "alarm_code": null,
      "alarm_message": null,
      "created_at": "2025-01-21 10:30:00",
      "updated_at": "2025-01-21 14:15:00",
      "created_by": "Administrator",
      "modified_by": "Administrator"
    },
    "message": "Successfully retrieved CNC data record"
  }
}
```

### 3. Get Equipment List

**Endpoint:** `get_iot_equipment_list`

**Method:** GET or POST

**Description:** Retrieves a list of unique equipment IDs from all CNC data records.

**Parameters:** None

**Example Request:**
```bash
curl "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify.get_iot_equipment_list"
```

**Response Format:**
```json
{
  "message": {
    "success": true,
    "data": [
      "CNC001",
      "CNC002",
      "CNC003",
      "CNC004"
    ],
    "count": 4,
    "message": "Successfully retrieved 4 unique equipment IDs"
  }
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique identifier for the CNC data record |
| `equipment_id` | String | Equipment identifier/serial number |
| `workpiece_count` | Integer | Number of workpieces processed |
| `runtime` | String | Total runtime of the equipment |
| `cutting_time` | String | Actual cutting/machining time |
| `cnc_model` | String | CNC machine model |
| `current_tool_no` | String | Currently active tool number |
| `operation_mode` | String | Operating mode (AUTO/MANUAL/etc.) |
| `run_mode` | String | Run mode (CONTINUOUS/SINGLE/etc.) |
| `rapid_override` | String | Rapid movement override percentage |
| `spindle_actual_rpm` | String | Actual spindle rotation speed |
| `feed_actual_rate` | String | Actual feed rate |
| `spindle_load` | String | Spindle load percentage |
| `x_axis_load` | String | X-axis load percentage |
| `y_axis_load` | String | Y-axis load percentage |
| `z_axis_load` | String | Z-axis load percentage |
| `alarm_code` | String | Alarm/error code (if any) |
| `alarm_message` | String | Alarm/error description (if any) |
| `created_at` | DateTime | Record creation timestamp |
| `updated_at` | DateTime | Last modification timestamp |

## Error Handling

All endpoints return a consistent error format:

```json
{
  "message": {
    "success": false,
    "data": null,
    "message": "Error description here"
  }
}
```

Common error scenarios:
- **Invalid parameters**: Validation errors for invalid input
- **Record not found**: When requesting a specific record that doesn't exist
- **Module not installed**: When the IoT Management module is not available
- **Database errors**: Internal server errors

## Usage Examples

### Python Example
```python
import requests

base_url = "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify"

# Get all equipment IDs
response = requests.get(f"{base_url}.get_iot_equipment_list")
equipment_list = response.json()["message"]["data"]

# Get data for first equipment
if equipment_list:
    equipment_id = equipment_list[0]
    response = requests.get(f"{base_url}.get_iot_cnc_data", params={
        "equipment_id": equipment_id,
        "limit": 10
    })
    cnc_data = response.json()["message"]["data"]
    print(f"Found {len(cnc_data)} records for equipment {equipment_id}")
```

### JavaScript Example
```javascript
const baseUrl = "http://iot.datawits.net:8000/api/method/frappe.integrations.api_dify";

// Fetch CNC data with async/await
async function getCNCData(equipmentId = null, limit = 50, offset = 0) {
    const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
    });
    
    if (equipmentId) {
        params.append('equipment_id', equipmentId);
    }
    
    try {
        const response = await fetch(`${baseUrl}.get_iot_cnc_data?${params}`);
        const result = await response.json();
        
        if (result.message.success) {
            return result.message.data;
        } else {
            throw new Error(result.message.message);
        }
    } catch (error) {
        console.error('Error fetching CNC data:', error);
        throw error;
    }
}

// Usage
getCNCData('CNC001', 10, 0)
    .then(data => console.log('CNC data:', data))
    .catch(error => console.error('Failed to fetch data:', error));
```

## Rate Limiting

Currently, there are no explicit rate limits on these APIs. However, the `limit` parameter is capped at 1000 records per request to prevent excessive load on the server.

## Security Considerations

- These APIs are currently open to guest access for demonstration purposes
- In production, consider implementing proper authentication and authorization
- Validate and sanitize all input parameters
- Monitor API usage for potential abuse

## Support

For questions or issues with these APIs, please contact the development team or refer to the Frappe framework documentation for general API usage patterns. 