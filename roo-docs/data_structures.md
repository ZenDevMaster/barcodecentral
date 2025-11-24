# Barcode Central - Data Structures

## Overview

This document defines all data structures used in the Barcode Central application, including JSON file formats, in-memory data models, and API request/response schemas.

## File-Based Storage

### Environment Variables (.env)

**Purpose**: Store application configuration and credentials

**Location**: Project root directory

**Format**: Key-value pairs

**Structure**:
```env
# Authentication
LOGIN_USER=admin
LOGIN_PASSWORD=secure_password_here

# Flask Configuration
FLASK_SECRET_KEY=random_secret_key_minimum_32_characters_long
FLASK_ENV=production
FLASK_DEBUG=False

# Application Settings
SESSION_TIMEOUT=3600
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Preview Settings
PREVIEW_CLEANUP_DAYS=7
PREVIEW_CLEANUP_ENABLED=True

# History Settings
HISTORY_MAX_ENTRIES=1000
HISTORY_ROTATION_ENABLED=True

# Labelary API
LABELARY_API_URL=http://api.labelary.com/v1/printers
LABELARY_DEFAULT_DPI=203
LABELARY_TIMEOUT=10

# Printer Settings
PRINTER_CONNECTION_TIMEOUT=5
PRINTER_STATUS_CACHE_TTL=300
```

**Validation Rules**:
- `LOGIN_USER`: Required, 3-50 characters, alphanumeric
- `LOGIN_PASSWORD`: Required, minimum 8 characters
- `FLASK_SECRET_KEY`: Required, minimum 32 characters
- `SESSION_TIMEOUT`: Integer, 300-86400 seconds
- `PREVIEW_CLEANUP_DAYS`: Integer, 1-365 days
- `HISTORY_MAX_ENTRIES`: Integer, 100-10000 entries

**Security Notes**:
- Never commit `.env` to version control
- Use `.env.example` as template
- Rotate `FLASK_SECRET_KEY` periodically
- Use strong passwords (12+ characters, mixed case, numbers, symbols)

---

### Printer Configuration (printers.json)

**Purpose**: Define available printers and their capabilities

**Location**: Project root directory

**Format**: JSON array of printer objects

**Structure**:
```json
{
  "printers": [
    {
      "name": "Warehouse Printer",
      "ip": "192.168.1.100",
      "port": 9100,
      "supported_sizes": ["4x6", "4x3"],
      "dpi": 203,
      "description": "Main warehouse shipping label printer",
      "enabled": true,
      "default": true
    },
    {
      "name": "Office Printer",
      "ip": "192.168.1.101",
      "port": 9100,
      "supported_sizes": ["2x1", "4x2"],
      "dpi": 300,
      "description": "Office product label printer",
      "enabled": true,
      "default": false
    },
    {
      "name": "Backup Printer",
      "ip": "192.168.1.102",
      "port": 9100,
      "supported_sizes": ["4x6", "4x3", "2x1"],
      "dpi": 203,
      "description": "Backup printer for all label types",
      "enabled": false,
      "default": false
    }
  ],
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-11-24T01:45:00Z",
    "updated_by": "admin"
  }
}
```

**Field Definitions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique printer identifier |
| `ip` | string | Yes | Printer IP address (IPv4) |
| `port` | integer | Yes | TCP port (typically 9100) |
| `supported_sizes` | array[string] | Yes | Supported label sizes (e.g., "4x6") |
| `dpi` | integer | Yes | Printer resolution (203, 300, 600) |
| `description` | string | No | Human-readable description |
| `enabled` | boolean | No | Whether printer is active (default: true) |
| `default` | boolean | No | Default printer selection (default: false) |

**Validation Rules**:
- `name`: Unique, 1-100 characters
- `ip`: Valid IPv4 address format
- `port`: Integer, 1-65535
- `supported_sizes`: Non-empty array, valid size format (WxH)
- `dpi`: One of [203, 300, 600]
- Only one printer can have `default: true`

**Label Size Format**:
- Format: `{width}x{height}` in inches
- Examples: `4x6`, `2x1`, `4x3`, `3x2`
- Width and height must be positive numbers

**Example Operations**:

Add printer:
```json
{
  "name": "New Printer",
  "ip": "192.168.1.103",
  "port": 9100,
  "supported_sizes": ["4x6"],
  "dpi": 203,
  "enabled": true
}
```

Update printer:
```json
{
  "name": "Warehouse Printer",
  "enabled": false
}
```

---

### Print History (history.json)

**Purpose**: Log all print jobs for auditing and reprinting

**Location**: Project root directory

**Format**: JSON array of history entries

**Structure**:
```json
{
  "entries": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-11-24T01:45:00.123Z",
      "user": "admin",
      "template": "shipping_label.zpl.j2",
      "template_name": "Shipping Label",
      "variables": {
        "name": "John Doe",
        "address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "tracking": "1Z999AA10123456784"
      },
      "printer": "Warehouse Printer",
      "printer_ip": "192.168.1.100",
      "quantity": 5,
      "label_size": "4x6",
      "dpi": 203,
      "preview_path": "previews/20251124_014500_550e8400.png",
      "zpl_code": "^XA\n^FO50,50^A0N,50,50^FDJohn Doe^FS\n...",
      "status": "success",
      "error": null,
      "duration_ms": 234
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "timestamp": "2025-11-24T01:50:00.456Z",
      "user": "admin",
      "template": "product_label.zpl.j2",
      "template_name": "Product Label",
      "variables": {
        "sku": "PROD-12345",
        "name": "Widget Pro",
        "price": "29.99"
      },
      "printer": "Office Printer",
      "printer_ip": "192.168.1.101",
      "quantity": 10,
      "label_size": "2x1",
      "dpi": 300,
      "preview_path": "previews/20251124_015000_660e8400.png",
      "zpl_code": "^XA\n^FO20,20^A0N,30,30^FDPROD-12345^FS\n...",
      "status": "success",
      "error": null,
      "duration_ms": 189
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "timestamp": "2025-11-24T02:00:00.789Z",
      "user": "admin",
      "template": "shipping_label.zpl.j2",
      "template_name": "Shipping Label",
      "variables": {
        "name": "Jane Smith",
        "address": "456 Oak Ave"
      },
      "printer": "Warehouse Printer",
      "printer_ip": "192.168.1.100",
      "quantity": 1,
      "label_size": "4x6",
      "dpi": 203,
      "preview_path": "previews/20251124_020000_770e8400.png",
      "zpl_code": "^XA\n^FO50,50^A0N,50,50^FDJane Smith^FS\n...",
      "status": "failed",
      "error": "Printer unreachable: Connection timeout after 5 seconds",
      "duration_ms": 5012
    }
  ],
  "metadata": {
    "version": "1.0",
    "total_entries": 847,
    "oldest_entry": "2025-10-15T08:30:00Z",
    "newest_entry": "2025-11-24T02:00:00Z",
    "last_rotation": "2025-11-20T00:00:00Z"
  }
}
```

**Field Definitions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique job identifier |
| `timestamp` | string (ISO 8601) | Yes | Job creation time (UTC) |
| `user` | string | Yes | Username who initiated job |
| `template` | string | Yes | Template filename |
| `template_name` | string | No | Human-readable template name |
| `variables` | object | Yes | Template variables used |
| `printer` | string | Yes | Printer name |
| `printer_ip` | string | Yes | Printer IP at time of print |
| `quantity` | integer | Yes | Number of labels printed |
| `label_size` | string | Yes | Label size (e.g., "4x6") |
| `dpi` | integer | Yes | Printer DPI used |
| `preview_path` | string | No | Path to preview image |
| `zpl_code` | string | Yes | Generated ZPL code |
| `status` | string | Yes | Job status: "success" or "failed" |
| `error` | string | No | Error message if failed |
| `duration_ms` | integer | No | Job duration in milliseconds |

**Validation Rules**:
- `id`: Valid UUID v4 format
- `timestamp`: Valid ISO 8601 format with timezone
- `user`: 1-50 characters
- `template`: Valid filename ending in `.zpl.j2`
- `variables`: Valid JSON object
- `quantity`: Integer, 1-1000
- `label_size`: Valid size format (WxH)
- `dpi`: One of [203, 300, 600]
- `status`: One of ["success", "failed"]

**Rotation Logic**:
- Keep last 1000 entries (configurable)
- When adding entry 1001, remove oldest entry
- Update `metadata.last_rotation` timestamp
- Delete associated preview image if exists
- Maintain chronological order (newest first)

**Indexing Strategy**:
- Primary index: `id` (unique)
- Secondary indexes: `timestamp`, `user`, `template`, `printer`
- For efficient filtering and pagination

---

### Template Metadata

**Purpose**: Store template information within ZPL files

**Location**: Embedded in `*.zpl.j2` files as comments

**Format**: ZPL comments with key-value pairs

**Structure**:
```zpl
^XA
^FX ===== TEMPLATE METADATA =====
^FX NAME: Shipping Label
^FX DESCRIPTION: Standard 4x6 shipping label with tracking barcode
^FX SIZE: 4x6
^FX DPI: 203
^FX VARIABLES: name, address, city, state, zip, tracking
^FX AUTHOR: admin
^FX CREATED: 2025-11-20T10:30:00Z
^FX MODIFIED: 2025-11-23T15:45:00Z
^FX VERSION: 1.2
^FX ===== END METADATA =====

^FX Label content starts here
^FO50,50^A0N,50,50^FD{{ name }}^FS
^FO50,120^A0N,40,40^FD{{ address }}^FS
^FO50,180^A0N,40,40^FD{{ city }}, {{ state }} {{ zip }}^FS
^FO50,250^BY3^BCN,100,Y,N,N^FD{{ tracking }}^FS
^XZ
```

**Metadata Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `NAME` | string | Yes | Template display name |
| `DESCRIPTION` | string | No | Template description |
| `SIZE` | string | Yes | Label size (e.g., "4x6") |
| `DPI` | integer | No | Recommended DPI (default: 203) |
| `VARIABLES` | string | Yes | Comma-separated variable names |
| `AUTHOR` | string | No | Template creator |
| `CREATED` | string | No | Creation timestamp (ISO 8601) |
| `MODIFIED` | string | No | Last modification timestamp |
| `VERSION` | string | No | Template version |

**Parsing Rules**:
- Metadata must be within first 50 lines
- Each metadata line starts with `^FX`
- Format: `^FX KEY: value`
- Keys are case-insensitive
- Values are trimmed of whitespace
- Multiple values separated by commas

**Variable Extraction**:
- Parse Jinja2 syntax: `{{ variable_name }}`
- Extract unique variable names
- Validate against VARIABLES metadata
- Warn if mismatch detected

---

## In-Memory Data Models

### User Session

**Purpose**: Track authenticated user state

**Storage**: Flask session (encrypted cookie)

**Structure**:
```python
{
    "user_id": "admin",
    "login_time": "2025-11-24T01:45:00Z",
    "last_activity": "2025-11-24T02:30:00Z",
    "session_id": "abc123def456",
    "preferences": {
        "default_printer": "Warehouse Printer",
        "default_quantity": 1,
        "show_preview": True
    }
}
```

**Field Definitions**:

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Username from .env |
| `login_time` | string | Session creation time (ISO 8601) |
| `last_activity` | string | Last request time (ISO 8601) |
| `session_id` | string | Unique session identifier |
| `preferences` | object | User preferences (optional) |

**Session Lifecycle**:
1. Created on successful login
2. Updated on each request (last_activity)
3. Validated on protected routes
4. Expired after SESSION_TIMEOUT seconds of inactivity
5. Destroyed on logout

---

### Template Object

**Purpose**: Represent a ZPL template in memory

**Structure**:
```python
{
    "filename": "shipping_label.zpl.j2",
    "path": "/app/templates_zpl/shipping_label.zpl.j2",
    "name": "Shipping Label",
    "description": "Standard 4x6 shipping label",
    "label_size": "4x6",
    "dpi": 203,
    "variables": ["name", "address", "city", "state", "zip", "tracking"],
    "content": "^XA\n^FO50,50^A0N,50,50^FD{{ name }}^FS\n...",
    "metadata": {
        "author": "admin",
        "created": "2025-11-20T10:30:00Z",
        "modified": "2025-11-23T15:45:00Z",
        "version": "1.2"
    },
    "file_stats": {
        "size_bytes": 1024,
        "created": "2025-11-20T10:30:00Z",
        "modified": "2025-11-23T15:45:00Z"
    }
}
```

---

### Printer Object

**Purpose**: Represent a printer configuration in memory

**Structure**:
```python
{
    "name": "Warehouse Printer",
    "ip": "192.168.1.100",
    "port": 9100,
    "supported_sizes": ["4x6", "4x3"],
    "dpi": 203,
    "description": "Main warehouse shipping label printer",
    "enabled": True,
    "default": True,
    "status": {
        "online": True,
        "last_checked": "2025-11-24T01:45:00Z",
        "response_time_ms": 45,
        "error": None
    }
}
```

**Status Caching**:
- Status cached for 5 minutes (configurable)
- Refreshed on explicit status check
- Cleared on printer configuration change

---

### Print Job Object

**Purpose**: Represent a print job in progress

**Structure**:
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-11-24T01:45:00Z",
    "user": "admin",
    "template": {
        "filename": "shipping_label.zpl.j2",
        "name": "Shipping Label"
    },
    "variables": {
        "name": "John Doe",
        "address": "123 Main St"
    },
    "printer": {
        "name": "Warehouse Printer",
        "ip": "192.168.1.100",
        "port": 9100
    },
    "quantity": 5,
    "label_size": "4x6",
    "dpi": 203,
    "preview_path": "previews/20251124_014500_550e8400.png",
    "zpl_code": "^XA\n...",
    "status": "pending",
    "progress": {
        "sent": 0,
        "total": 5,
        "errors": []
    }
}
```

---

### Preview Request Object

**Purpose**: Represent a preview generation request

**Structure**:
```python
{
    "zpl": "^XA\n^FO50,50^A0N,50,50^FDTest^FS\n^XZ",
    "label_size": "4x6",
    "dpi": 203,
    "format": "png",
    "width_inches": 4,
    "height_inches": 6,
    "rotate": 0,
    "density": 8
}
```

**Labelary API Mapping**:
- `dpi`: Printer resolution (203, 300, 600)
- `width_inches`: Label width in inches
- `height_inches`: Label height in inches
- `rotate`: Rotation angle (0, 90, 180, 270)
- `density`: Darkness (0-15, default: 8)

---

## API Request/Response Schemas

### Login Request

```json
{
  "username": "admin",
  "password": "password123"
}
```

**Validation**:
- `username`: Required, string, 1-50 characters
- `password`: Required, string, 1-100 characters

---

### Template Create/Update Request

```json
{
  "filename": "new_label.zpl.j2",
  "name": "New Label",
  "description": "Custom label template",
  "label_size": "4x6",
  "content": "^XA\n^FO50,50^A0N,50,50^FDTest^FS\n^XZ"
}
```

**Validation**:
- `filename`: Required for create, must end with `.zpl.j2`
- `name`: Required, 1-100 characters
- `description`: Optional, max 500 characters
- `label_size`: Required, valid size format
- `content`: Required, valid ZPL syntax

---

### Print Request

```json
{
  "template": "shipping_label.zpl.j2",
  "variables": {
    "name": "John Doe",
    "address": "123 Main St"
  },
  "printer": "Warehouse Printer",
  "quantity": 5,
  "preview_path": "previews/20251124_014500_abc123.png"
}
```

**Validation**:
- `template`: Required, must exist
- `variables`: Required, object with all required variables
- `printer`: Required, must exist and be enabled
- `quantity`: Required, integer 1-1000
- `preview_path`: Optional, must exist if provided

---

### Preview Request

```json
{
  "zpl": "^XA\n^FO50,50^A0N,50,50^FDTest^FS\n^XZ",
  "label_size": "4x6",
  "dpi": 203,
  "format": "png"
}
```

**Validation**:
- `zpl`: Required, non-empty string
- `label_size`: Required, valid size format
- `dpi`: Optional, one of [203, 300, 600], default: 203
- `format`: Optional, one of ["png", "pdf"], default: "png"

---

## File Naming Conventions

### Preview Files

**Format**: `{date}_{time}_{uuid}.{ext}`

**Example**: `20251124_014500_550e8400.png`

**Components**:
- `date`: YYYYMMDD format
- `time`: HHMMSS format (24-hour)
- `uuid`: First 8 characters of UUID
- `ext`: File extension (png, pdf)

**Purpose**: Unique, sortable, human-readable filenames

---

### Template Files

**Format**: `{name}.zpl.j2`

**Example**: `shipping_label.zpl.j2`

**Rules**:
- Lowercase with underscores
- No spaces or special characters
- Must end with `.zpl.j2`
- Maximum 100 characters

---

## Data Validation

### Common Validation Rules

**Email Format** (if implemented):
```regex
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

**IP Address Format**:
```regex
^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$
```

**Label Size Format**:
```regex
^\d+(\.\d+)?x\d+(\.\d+)?$
```

**UUID Format**:
```regex
^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
```

**ISO 8601 Timestamp**:
```regex
^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$
```

---

## Data Migration

### Version 1.0 to 1.1 (Example)

If data structure changes are needed:

**Migration Script**:
```python
def migrate_history_v1_to_v1_1(history_data):
    """Add duration_ms field to existing entries"""
    for entry in history_data["entries"]:
        if "duration_ms" not in entry:
            entry["duration_ms"] = None
    
    history_data["metadata"]["version"] = "1.1"
    return history_data
```

**Backward Compatibility**:
- Always add new fields as optional
- Never remove existing fields
- Provide default values for missing fields
- Document migration path

---

## Data Backup

### Backup Structure

```json
{
  "backup_date": "2025-11-24T01:45:00Z",
  "version": "1.0",
  "files": {
    "printers": { ... },
    "history": { ... },
    "templates": [
      {
        "filename": "shipping_label.zpl.j2",
        "content": "..."
      }
    ]
  }
}
```

**Backup Schedule**:
- Daily: History and configuration
- Weekly: Full backup including templates
- Monthly: Archive backup

---

## Conclusion

These data structures provide a complete specification for all data storage and exchange in the Barcode Central application. All structures are designed for simplicity, maintainability, and future extensibility.