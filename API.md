# Barcode Central - API Reference

## Overview

Barcode Central provides a RESTful API for managing ZPL label templates, printers, and print jobs. All API endpoints return JSON responses and use session-based authentication.

## Base URL

- **Development**: `http://localhost:5000`
- **Production**: `http://<server-ip>:8000`

## Authentication

All API endpoints (except `/login` and `/api/health`) require authentication via session cookies.

### Login

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  -c cookies.txt
```

### Using Session Cookie

```bash
curl http://localhost:5000/api/templates \
  -b cookies.txt
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "details": "Optional additional details"
}
```

## HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Authentication Endpoints

### POST /login

Authenticate user and create session.

**Request:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  -c cookies.txt
```

### GET /logout

End user session.

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## Template Endpoints

### GET /api/templates

List all ZPL templates.

**Query Parameters:**
- `include_content` (optional): Include template content (default: false)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "filename": "shipping_label.zpl.j2",
        "name": "Shipping Label",
        "description": "Standard shipping label",
        "size": "4x6",
        "variables": ["order_number", "customer_name", "address"],
        "created": "2024-01-15T10:00:00Z",
        "modified": "2024-01-20T15:30:00Z"
      }
    ],
    "count": 1
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/templates \
  -b cookies.txt
```

```python
import requests

session = requests.Session()
session.post('http://localhost:5000/login', 
             json={'username': 'admin', 'password': 'admin'})

response = session.get('http://localhost:5000/api/templates')
templates = response.json()['data']['templates']
```

### GET /api/templates/<filename>

Get specific template details and content.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "template": {
      "filename": "shipping_label.zpl.j2",
      "name": "Shipping Label",
      "content": "^XA\n^FO50,50^FD{{ order_number }}^FS\n^XZ",
      "variables": ["order_number"],
      "size": "4x6"
    }
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/templates/shipping_label.zpl.j2 \
  -b cookies.txt
```

### POST /api/templates

Create a new template.

**Request:**
```json
{
  "filename": "new_template.zpl.j2",
  "content": "^XA\n^FO50,50^FD{{ text }}^FS\n^XZ",
  "metadata": {
    "name": "New Template",
    "description": "Template description",
    "size": "4x6"
  }
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Template created successfully",
  "data": {
    "filename": "new_template.zpl.j2"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/templates \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "filename": "test.zpl.j2",
    "content": "^XA\n^FO50,50^FD{{ text }}^FS\n^XZ",
    "metadata": {"name": "Test", "size": "4x6"}
  }'
```

### PUT /api/templates/<filename>

Update existing template.

**Request:**
```json
{
  "content": "^XA\n^FO50,50^FD{{ updated_text }}^FS\n^XZ",
  "metadata": {
    "name": "Updated Template",
    "size": "4x6"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Template updated successfully"
}
```

### DELETE /api/templates/<filename>

Delete a template.

**Response (200):**
```json
{
  "success": true,
  "message": "Template deleted successfully"
}
```

### POST /api/templates/<filename>/render

Render template with variables.

**Request:**
```json
{
  "variables": {
    "order_number": "12345",
    "customer_name": "John Doe"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "zpl": "^XA\n^FO50,50^FD12345^FS\n^XZ"
  }
}
```

### POST /api/templates/validate

Validate template content.

**Request:**
```json
{
  "content": "^XA\n^FO50,50^FDTest^FS\n^XZ"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "error": null
  }
}
```

### GET /api/templates/<filename>/variables

Extract variables from template.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "variables": ["order_number", "customer_name", "address"]
  }
}
```

---

## Printer Endpoints

### GET /api/printers

List all configured printers.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "printers": [
      {
        "id": "warehouse-printer-01",
        "name": "Warehouse Printer",
        "ip": "192.168.1.100",
        "port": 9100,
        "supported_sizes": ["4x6", "4x2"],
        "dpi": 203,
        "enabled": true
      }
    ]
  }
}
```

### GET /api/printers/<id>

Get specific printer details.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "printer": {
      "id": "warehouse-printer-01",
      "name": "Warehouse Printer",
      "ip": "192.168.1.100",
      "port": 9100,
      "supported_sizes": ["4x6"],
      "dpi": 203,
      "enabled": true
    }
  }
}
```

### POST /api/printers

Add a new printer.

**Request:**
```json
{
  "id": "new-printer",
  "name": "New Printer",
  "ip": "192.168.1.101",
  "port": 9100,
  "supported_sizes": ["4x6", "4x2"],
  "dpi": 203,
  "enabled": true,
  "description": "Optional description"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Printer added successfully"
}
```

### PUT /api/printers/<id>

Update printer configuration.

**Request:**
```json
{
  "name": "Updated Printer Name",
  "enabled": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Printer updated successfully"
}
```

### DELETE /api/printers/<id>

Delete a printer.

**Response (200):**
```json
{
  "success": true,
  "message": "Printer deleted successfully"
}
```

### POST /api/printers/<id>/test

Test printer connection.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "connected": true,
    "message": "Connection successful to 192.168.1.100:9100"
  }
}
```

### POST /api/printers/<id>/validate

Validate printer compatibility with label size.

**Request:**
```json
{
  "label_size": "4x6"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "compatible": true,
    "message": "Printer is compatible"
  }
}
```

---

## Preview Endpoints

### POST /api/preview/generate

Generate label preview image.

**Request:**
```json
{
  "zpl": "^XA\n^FO50,50^FDTest^FS\n^XZ",
  "label_size": "4x6",
  "dpi": 203
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "preview_url": "/api/preview/abc123.png",
    "filename": "abc123.png"
  }
}
```

### GET /api/preview/<filename>

Retrieve generated preview image.

**Response (200):**
Returns PNG image file.

### POST /api/preview/cleanup

Clean up old preview files.

**Response (200):**
```json
{
  "success": true,
  "message": "Cleaned up 5 old preview files"
}
```

---

## Print Endpoints

### POST /api/print

Execute print job.

**Request:**
```json
{
  "template": "shipping_label.zpl.j2",
  "printer_id": "warehouse-printer-01",
  "variables": {
    "order_number": "12345",
    "customer_name": "John Doe"
  },
  "copies": 1,
  "preview_only": false
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Print job completed successfully",
  "data": {
    "job_id": "hist-abc123",
    "preview_url": "/api/preview/abc123.png"
  }
}
```

### POST /api/print/validate

Validate print job before execution.

**Request:**
```json
{
  "template": "shipping_label.zpl.j2",
  "printer_id": "warehouse-printer-01",
  "variables": {"order_number": "12345"}
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "issues": []
  }
}
```

---

## History Endpoints

### GET /api/history

List print job history with pagination and filtering.

**Query Parameters:**
- `limit` (optional): Max entries to return (default: 100, max: 500)
- `offset` (optional): Number of entries to skip (default: 0)
- `template` (optional): Filter by template name
- `printer_id` (optional): Filter by printer ID
- `status` (optional): Filter by status (success/failed)
- `start_date` (optional): Filter by start date (ISO 8601)
- `end_date` (optional): Filter by end date (ISO 8601)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "id": "hist-abc123",
        "timestamp": "2024-01-20T15:30:00Z",
        "template": "shipping_label.zpl.j2",
        "printer_id": "warehouse-printer-01",
        "printer_name": "Warehouse Printer",
        "variables": {"order_number": "12345"},
        "copies": 1,
        "status": "success"
      }
    ],
    "total": 150,
    "limit": 100,
    "offset": 0
  }
}
```

**Example:**
```bash
curl "http://localhost:5000/api/history?limit=10&status=success" \
  -b cookies.txt
```

### GET /api/history/<id>

Get specific history entry.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "entry": {
      "id": "hist-abc123",
      "timestamp": "2024-01-20T15:30:00Z",
      "template": "shipping_label.zpl.j2",
      "variables": {"order_number": "12345"},
      "zpl_content": "^XA\n^FO50,50^FD12345^FS\n^XZ"
    }
  }
}
```

### DELETE /api/history/<id>

Delete history entry.

**Response (200):**
```json
{
  "success": true,
  "message": "History entry deleted successfully"
}
```

### POST /api/history/<id>/reprint

Reprint from history entry.

**Request (optional):**
```json
{
  "variables": {
    "order_number": "54321"
  },
  "copies": 2
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Reprint completed successfully",
  "data": {
    "job_id": "hist-xyz789"
  }
}
```

### GET /api/history/search

Search history entries.

**Query Parameters:**
- `q` (required): Search query
- `field` (optional): Specific field to search

**Response (200):**
```json
{
  "success": true,
  "data": {
    "results": [...],
    "count": 5
  }
}
```

### GET /api/history/statistics

Get usage statistics.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "statistics": {
      "total_jobs": 1000,
      "successful_jobs": 950,
      "failed_jobs": 50,
      "success_rate": 95.0,
      "most_used_template": "shipping_label.zpl.j2",
      "most_used_printer": "warehouse-printer-01"
    }
  }
}
```

### POST /api/history/cleanup

Clean up old history entries.

**Request:**
```json
{
  "days": 30
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Deleted 50 entries older than 30 days"
}
```

### GET /api/history/export

Export history data.

**Query Parameters:**
- Same as GET /api/history for filtering

**Response (200):**
```json
{
  "success": true,
  "data": {
    "export": {
      "entries": [...],
      "exported_at": "2024-01-20T15:30:00Z",
      "total_entries": 100
    }
  }
}
```

---

## Health Check

### GET /api/health

Check application health (no authentication required).

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T15:30:00Z",
  "service": "barcode-central"
}
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Invalid request data",
  "details": "Missing required field: template"
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": "Authentication required"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "Template 'nonexistent.zpl.j2' not found"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "Internal server error",
  "details": "Database connection failed"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting in production environments.

---

## Best Practices

1. **Always validate input** before sending requests
2. **Handle errors gracefully** in your client code
3. **Use preview mode** before printing to verify output
4. **Store session cookies securely**
5. **Implement retry logic** for network failures
6. **Log all print jobs** for audit purposes

---

## Complete Example Workflow

```python
import requests

# Initialize session
session = requests.Session()
base_url = 'http://localhost:5000'

# 1. Login
session.post(f'{base_url}/login', json={
    'username': 'admin',
    'password': 'admin'
})

# 2. List templates
templates = session.get(f'{base_url}/api/templates').json()
template_name = templates['data']['templates'][0]['filename']

# 3. Render template
rendered = session.post(
    f'{base_url}/api/templates/{template_name}/render',
    json={'variables': {'text': 'Hello World'}}
).json()

# 4. Generate preview
preview = session.post(f'{base_url}/api/preview/generate', json={
    'zpl': rendered['data']['zpl'],
    'label_size': '4x6',
    'dpi': 203
}).json()

# 5. Print
result = session.post(f'{base_url}/api/print', json={
    'template': template_name,
    'printer_id': 'warehouse-printer-01',
    'variables': {'text': 'Hello World'},
    'copies': 1
}).json()

print(f"Print job completed: {result['data']['job_id']}")
```

---

## Support

For issues or questions, please refer to:
- [User Guide](USER_GUIDE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)