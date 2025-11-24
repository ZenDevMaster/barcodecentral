# Barcode Central - API Endpoints

## Overview

This document specifies all HTTP endpoints for the Barcode Central application. The API follows RESTful conventions where applicable and uses session-based authentication.

## Base URL

- **Development**: `http://localhost:5000`
- **Production**: `http://<server-ip>:8000`

## Authentication

All endpoints except `/login` and `/health` require authentication. Authentication is handled via Flask-Login session cookies.

### Session Cookie
- **Name**: `session`
- **Attributes**: `HttpOnly`, `Secure` (in production), `SameSite=Lax`
- **Lifetime**: Configurable (default: 1 hour)

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "details": { ... }
}
```

## Endpoints

---

## Authentication Endpoints

### Login

**Endpoint**: `POST /login`

**Description**: Authenticate user and create session

**Authentication**: Not required

**Request Body**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Login successful",
  "redirect": "/dashboard"
}
```

**Response** (401 Unauthorized):
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}' \
  -c cookies.txt
```

---

### Logout

**Endpoint**: `POST /logout`

**Description**: End user session

**Authentication**: Required

**Request Body**: None

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Logged out successfully",
  "redirect": "/login"
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/logout \
  -b cookies.txt
```

---

### Check Session

**Endpoint**: `GET /api/session`

**Description**: Verify current session status

**Authentication**: Required

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "user": "admin",
    "login_time": "2025-11-24T01:45:00Z",
    "expires_at": "2025-11-24T02:45:00Z"
  }
}
```

**Response** (401 Unauthorized):
```json
{
  "success": false,
  "error": "Not authenticated"
}
```

---

## Template Endpoints

### List Templates

**Endpoint**: `GET /api/templates`

**Description**: Get list of all available ZPL templates

**Authentication**: Required

**Query Parameters**:
- `include_content` (optional, boolean): Include template content in response (default: false)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "filename": "shipping_label.zpl.j2",
        "name": "Shipping Label",
        "description": "Standard 4x6 shipping label",
        "label_size": "4x6",
        "variables": ["name", "address", "city", "zip", "tracking"],
        "created": "2025-11-20T10:30:00Z",
        "modified": "2025-11-23T15:45:00Z"
      },
      {
        "filename": "product_label.zpl.j2",
        "name": "Product Label",
        "description": "2x1 product label with barcode",
        "label_size": "2x1",
        "variables": ["sku", "name", "price"],
        "created": "2025-11-21T09:00:00Z",
        "modified": "2025-11-21T09:00:00Z"
      }
    ],
    "count": 2
  }
}
```

**Example**:
```bash
curl -X GET http://localhost:5000/api/templates \
  -b cookies.txt
```

---

### Get Template

**Endpoint**: `GET /api/templates/{filename}`

**Description**: Get specific template details and content

**Authentication**: Required

**Path Parameters**:
- `filename`: Template filename (e.g., `shipping_label.zpl.j2`)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "filename": "shipping_label.zpl.j2",
    "name": "Shipping Label",
    "description": "Standard 4x6 shipping label",
    "label_size": "4x6",
    "variables": ["name", "address", "city", "zip", "tracking"],
    "content": "^XA\n^FO50,50^A0N,50,50^FD{{ name }}^FS\n...",
    "created": "2025-11-20T10:30:00Z",
    "modified": "2025-11-23T15:45:00Z"
  }
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Template not found"
}
```

**Example**:
```bash
curl -X GET http://localhost:5000/api/templates/shipping_label.zpl.j2 \
  -b cookies.txt
```

---

### Create Template

**Endpoint**: `POST /api/templates`

**Description**: Create a new ZPL template

**Authentication**: Required

**Request Body**:
```json
{
  "filename": "new_label.zpl.j2",
  "name": "New Label",
  "description": "Custom label template",
  "label_size": "4x6",
  "content": "^XA\n^FO50,50^A0N,50,50^FDTest^FS\n^XZ"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Template created successfully",
  "data": {
    "filename": "new_label.zpl.j2",
    "path": "/templates_zpl/new_label.zpl.j2"
  }
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Template already exists"
}
```

**Response** (422 Unprocessable Entity):
```json
{
  "success": false,
  "error": "Invalid ZPL syntax",
  "details": {
    "line": 5,
    "message": "Missing closing tag"
  }
}
```

---

### Update Template

**Endpoint**: `PUT /api/templates/{filename}`

**Description**: Update existing template

**Authentication**: Required

**Path Parameters**:
- `filename`: Template filename

**Request Body**:
```json
{
  "name": "Updated Label Name",
  "description": "Updated description",
  "label_size": "4x6",
  "content": "^XA\n^FO50,50^A0N,50,50^FDUpdated^FS\n^XZ"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Template updated successfully",
  "data": {
    "filename": "shipping_label.zpl.j2",
    "modified": "2025-11-24T01:45:00Z"
  }
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Template not found"
}
```

---

### Delete Template

**Endpoint**: `DELETE /api/templates/{filename}`

**Description**: Delete a template

**Authentication**: Required

**Path Parameters**:
- `filename`: Template filename

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Template deleted successfully"
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Template not found"
}
```

---

### Render Template

**Endpoint**: `POST /api/templates/{filename}/render`

**Description**: Render template with variables to generate ZPL code

**Authentication**: Required

**Path Parameters**:
- `filename`: Template filename

**Request Body**:
```json
{
  "variables": {
    "name": "John Doe",
    "address": "123 Main St",
    "city": "New York",
    "zip": "10001",
    "tracking": "1Z999AA10123456784"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "zpl": "^XA\n^FO50,50^A0N,50,50^FDJohn Doe^FS\n^FO50,120^A0N,40,40^FD123 Main St^FS\n...",
    "variables_used": ["name", "address", "city", "zip", "tracking"]
  }
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Missing required variables",
  "details": {
    "missing": ["name", "tracking"]
  }
}
```

---

## Printer Endpoints

### List Printers

**Endpoint**: `GET /api/printers`

**Description**: Get list of configured printers with status

**Authentication**: Required

**Query Parameters**:
- `check_status` (optional, boolean): Check printer connectivity (default: true)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "printers": [
      {
        "name": "Warehouse Printer",
        "ip": "192.168.1.100",
        "port": 9100,
        "supported_sizes": ["4x6", "4x3"],
        "dpi": 203,
        "status": "online",
        "last_checked": "2025-11-24T01:45:00Z"
      },
      {
        "name": "Office Printer",
        "ip": "192.168.1.101",
        "port": 9100,
        "supported_sizes": ["2x1", "4x2"],
        "dpi": 300,
        "status": "offline",
        "last_checked": "2025-11-24T01:45:00Z"
      }
    ],
    "count": 2
  }
}
```

**Example**:
```bash
curl -X GET http://localhost:5000/api/printers \
  -b cookies.txt
```

---

### Get Printer

**Endpoint**: `GET /api/printers/{name}`

**Description**: Get specific printer details

**Authentication**: Required

**Path Parameters**:
- `name`: Printer name (URL-encoded)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "name": "Warehouse Printer",
    "ip": "192.168.1.100",
    "port": 9100,
    "supported_sizes": ["4x6", "4x3"],
    "dpi": 203,
    "status": "online",
    "last_checked": "2025-11-24T01:45:00Z"
  }
}
```

---

### Validate Printer

**Endpoint**: `POST /api/printers/{name}/validate`

**Description**: Check printer connectivity and compatibility

**Authentication**: Required

**Path Parameters**:
- `name`: Printer name

**Request Body**:
```json
{
  "label_size": "4x6"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "reachable": true,
    "compatible": true,
    "warnings": []
  }
}
```

**Response** (200 OK with warnings):
```json
{
  "success": true,
  "data": {
    "reachable": true,
    "compatible": false,
    "warnings": [
      "Label size 4x6 not in printer's supported sizes [2x1, 4x2]",
      "Printing may result in clipped content"
    ]
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "success": false,
  "error": "Printer unreachable",
  "details": {
    "ip": "192.168.1.100",
    "port": 9100,
    "timeout": 5
  }
}
```

---

## Preview Endpoints

### Generate Preview

**Endpoint**: `POST /api/preview`

**Description**: Generate preview image of rendered ZPL label

**Authentication**: Required

**Request Body**:
```json
{
  "zpl": "^XA\n^FO50,50^A0N,50,50^FDTest Label^FS\n^XZ",
  "label_size": "4x6",
  "dpi": 203,
  "format": "png"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "preview_url": "/previews/20251124_014500_abc123.png",
    "preview_path": "previews/20251124_014500_abc123.png",
    "width": 812,
    "height": 1218,
    "expires_at": "2025-12-01T01:45:00Z"
  }
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid ZPL code",
  "details": {
    "message": "Labelary API returned error: Invalid command"
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "success": false,
  "error": "Preview service unavailable",
  "details": {
    "message": "Labelary API timeout"
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/api/preview \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"zpl":"^XA^FO50,50^A0N,50,50^FDTest^FS^XZ","label_size":"4x6","dpi":203}'
```

---

### Generate PDF Preview

**Endpoint**: `POST /api/preview/pdf`

**Description**: Generate PDF preview of rendered ZPL label

**Authentication**: Required

**Request Body**:
```json
{
  "zpl": "^XA\n^FO50,50^A0N,50,50^FDTest Label^FS\n^XZ",
  "label_size": "4x6",
  "dpi": 203
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "preview_url": "/previews/20251124_014500_abc123.pdf",
    "preview_path": "previews/20251124_014500_abc123.pdf",
    "expires_at": "2025-12-01T01:45:00Z"
  }
}
```

---

## Print Endpoints

### Print Label

**Endpoint**: `POST /api/print`

**Description**: Send ZPL code to printer

**Authentication**: Required

**Request Body**:
```json
{
  "template": "shipping_label.zpl.j2",
  "variables": {
    "name": "John Doe",
    "address": "123 Main St",
    "city": "New York",
    "zip": "10001",
    "tracking": "1Z999AA10123456784"
  },
  "printer": "Warehouse Printer",
  "quantity": 5,
  "preview_path": "previews/20251124_014500_abc123.png"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Print job sent successfully",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "printer": "Warehouse Printer",
    "quantity": 5,
    "timestamp": "2025-11-24T01:45:00Z"
  }
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid print request",
  "details": {
    "missing_fields": ["printer"]
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "success": false,
  "error": "Printer unavailable",
  "details": {
    "printer": "Warehouse Printer",
    "ip": "192.168.1.100",
    "message": "Connection timeout"
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/api/print \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "template": "shipping_label.zpl.j2",
    "variables": {"name": "John Doe"},
    "printer": "Warehouse Printer",
    "quantity": 1
  }'
```

---

### Test Print

**Endpoint**: `POST /api/print/test`

**Description**: Send test pattern to printer

**Authentication**: Required

**Request Body**:
```json
{
  "printer": "Warehouse Printer",
  "label_size": "4x6"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Test print sent successfully",
  "data": {
    "printer": "Warehouse Printer",
    "timestamp": "2025-11-24T01:45:00Z"
  }
}
```

---

## History Endpoints

### List History

**Endpoint**: `GET /api/history`

**Description**: Get print job history

**Authentication**: Required

**Query Parameters**:
- `page` (optional, integer): Page number (default: 1)
- `per_page` (optional, integer): Items per page (default: 100, max: 100)
- `template` (optional, string): Filter by template filename
- `printer` (optional, string): Filter by printer name
- `start_date` (optional, ISO 8601): Filter by start date
- `end_date` (optional, ISO 8601): Filter by end date

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2025-11-24T01:45:00Z",
        "user": "admin",
        "template": "shipping_label.zpl.j2",
        "variables": {
          "name": "John Doe",
          "address": "123 Main St"
        },
        "printer": "Warehouse Printer",
        "printer_ip": "192.168.1.100",
        "quantity": 5,
        "label_size": "4x6",
        "preview_path": "previews/20251124_014500_abc123.png",
        "status": "success",
        "error": null
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 100,
      "total": 150,
      "pages": 2
    }
  }
}
```

**Example**:
```bash
curl -X GET "http://localhost:5000/api/history?page=1&per_page=50&template=shipping_label.zpl.j2" \
  -b cookies.txt
```

---

### Get History Entry

**Endpoint**: `GET /api/history/{id}`

**Description**: Get specific history entry details

**Authentication**: Required

**Path Parameters**:
- `id`: History entry UUID

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-11-24T01:45:00Z",
    "user": "admin",
    "template": "shipping_label.zpl.j2",
    "variables": {
      "name": "John Doe",
      "address": "123 Main St",
      "city": "New York",
      "zip": "10001",
      "tracking": "1Z999AA10123456784"
    },
    "printer": "Warehouse Printer",
    "printer_ip": "192.168.1.100",
    "quantity": 5,
    "label_size": "4x6",
    "preview_path": "previews/20251124_014500_abc123.png",
    "status": "success",
    "error": null,
    "zpl_code": "^XA\n^FO50,50^A0N,50,50^FDJohn Doe^FS\n..."
  }
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "History entry not found"
}
```

---

### Reprint from History

**Endpoint**: `POST /api/history/{id}/reprint`

**Description**: Reprint a label from history

**Authentication**: Required

**Path Parameters**:
- `id`: History entry UUID

**Request Body**:
```json
{
  "printer": "Warehouse Printer",
  "quantity": 3
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Reprint job sent successfully",
  "data": {
    "job_id": "660e8400-e29b-41d4-a716-446655440001",
    "original_job_id": "550e8400-e29b-41d4-a716-446655440000",
    "printer": "Warehouse Printer",
    "quantity": 3,
    "timestamp": "2025-11-24T02:00:00Z"
  }
}
```

---

### Delete History Entry

**Endpoint**: `DELETE /api/history/{id}`

**Description**: Delete a history entry (admin only)

**Authentication**: Required

**Path Parameters**:
- `id`: History entry UUID

**Response** (200 OK):
```json
{
  "success": true,
  "message": "History entry deleted successfully"
}
```

---

## Utility Endpoints

### Health Check

**Endpoint**: `GET /health`

**Description**: Check application health status

**Authentication**: Not required

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-11-24T01:45:00Z",
    "version": "1.0.0",
    "services": {
      "templates": "ok",
      "printers": "ok",
      "history": "ok",
      "labelary": "ok"
    }
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "success": false,
  "data": {
    "status": "unhealthy",
    "timestamp": "2025-11-24T01:45:00Z",
    "version": "1.0.0",
    "services": {
      "templates": "ok",
      "printers": "ok",
      "history": "error",
      "labelary": "timeout"
    }
  }
}
```

---

### System Info

**Endpoint**: `GET /api/system/info`

**Description**: Get system information

**Authentication**: Required

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "python_version": "3.9.7",
    "flask_version": "2.3.0",
    "uptime_seconds": 86400,
    "template_count": 15,
    "printer_count": 3,
    "history_count": 847,
    "preview_count": 234,
    "disk_usage": {
      "previews_mb": 45.2,
      "history_mb": 2.1
    }
  }
}
```

---

## Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `BAD_REQUEST` | Invalid request parameters |
| 401 | `UNAUTHORIZED` | Authentication required |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Validation error |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | External service unavailable |

## Rate Limiting

Rate limiting is optional but recommended for production:

- **Preview Generation**: 60 requests per minute per user
- **Print Jobs**: 30 requests per minute per user
- **API Calls**: 300 requests per minute per user

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

## CORS Configuration

CORS is disabled by default. For API-only deployments, configure:

```python
CORS_ORIGINS = ["http://localhost:3000"]
CORS_METHODS = ["GET", "POST", "PUT", "DELETE"]
CORS_ALLOW_HEADERS = ["Content-Type", "Authorization"]
```

## Webhooks (Future Enhancement)

Webhook support for print job notifications:

**Endpoint**: `POST /api/webhooks`

**Request Body**:
```json
{
  "url": "https://example.com/webhook",
  "events": ["print.success", "print.failure"],
  "secret": "webhook_secret_key"
}
```

## API Versioning

Current version: `v1` (implicit)

Future versions will use URL prefix: `/api/v2/...`

## Testing Endpoints

Use the provided examples with `curl` or tools like Postman. Remember to:

1. Login first to get session cookie
2. Include cookie in subsequent requests
3. Use proper Content-Type headers
4. Handle error responses appropriately

## Conclusion

This API provides comprehensive functionality for managing ZPL templates, printers, and print jobs. All endpoints follow consistent patterns for requests, responses, and error handling.