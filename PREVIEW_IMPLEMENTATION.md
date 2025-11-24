# Preview and Printing Functionality Implementation

## Overview
This document summarizes the implementation of preview generation and complete printing workflow for Barcode Central (Phase 5).

## Implementation Date
November 24, 2024

## Files Created

### 1. Core Modules

#### `preview_generator.py`
- **PreviewGenerator** class for Labelary API integration
- Methods:
  - `generate_preview()` - Generate PNG/PDF preview from ZPL
  - `generate_pdf()` - Generate PDF preview
  - `save_preview()` - Generate and save preview to file
  - `get_preview_path()` - Get full path to preview file
  - `preview_exists()` - Check if preview exists
  - `cleanup_old_previews()` - Delete old preview files
- Features:
  - Labelary API integration (http://api.labelary.com)
  - Support for multiple DPI settings (152, 203, 300, 600)
  - Support for various label sizes (4x6, 4x2, etc.)
  - Local preview caching in `previews/` directory
  - UUID-based filename generation
  - Automatic cleanup of old previews

#### `utils/preview_utils.py`
Utility functions for preview operations:
- `parse_label_size()` - Parse "4x6" into (4.0, 6.0)
- `validate_label_size()` - Validate label size format
- `calculate_preview_dimensions()` - Calculate pixel dimensions
- `generate_preview_filename()` - Generate unique UUID filename
- `get_labelary_url()` - Construct Labelary API URL
- `map_printer_dpi_to_labelary()` - Map printer DPI to Labelary DPI
- `format_file_size()` - Format bytes to human-readable size
- `sanitize_preview_filename()` - Sanitize filenames
- `extract_label_size_from_template()` - Extract size from template metadata

### 2. Flask Blueprints

#### `blueprints/preview_bp.py`
Preview management endpoints:
- `POST /api/preview/generate` - Generate preview from ZPL or template
- `GET /api/preview/<filename>` - Serve preview image
- `POST /api/preview/pdf` - Generate PDF preview
- `DELETE /api/preview/<filename>` - Delete preview file
- `POST /api/preview/cleanup` - Cleanup old previews
- `GET /api/preview/status` - Get preview system status

#### `blueprints/print_bp.py`
Complete print workflow endpoints:
- `POST /api/print/` - Complete print workflow (render, preview, print)
- `POST /api/print/preview-only` - Render and preview without printing
- `GET /api/print/status/<job_id>` - Get print job status (placeholder)
- `POST /api/print/validate` - Validate print job without executing

### 3. Updated Files

#### `print_job.py`
Enhanced PrintJob class:
- Added `generate_preview` parameter to constructor
- Added `preview_filename` and `preview_url` attributes
- New method: `generate_preview_image()` - Generate preview from rendered ZPL
- Updated `execute()` to optionally generate preview
- Updated `to_dict()` to include preview information
- Updated factory function `create_print_job()` with preview support

#### `app.py`
- Registered `preview_bp` blueprint at `/api/preview`
- Registered `print_bp` blueprint at `/api/print`
- Added automatic creation of `previews/` directory on startup

### 4. Test Scripts

#### `test_preview.py`
Comprehensive test script with functions:
- `test_preview_from_template()` - Test preview from template
- `test_preview_from_zpl()` - Test preview from raw ZPL
- `test_pdf_generation()` - Test PDF generation
- `test_different_sizes()` - Test multiple label sizes
- `test_cleanup()` - Test cleanup functionality
- `run_all_tests()` - Run complete test suite

Usage:
```bash
# Run all tests
python test_preview.py --all

# Test specific template
python test_preview.py --template example.zpl.j2

# Test raw ZPL
python test_preview.py --zpl "^XA^FO50,50^FDTest^FS^XZ"

# Generate PDF
python test_preview.py --template example.zpl.j2 --pdf
```

## API Endpoints

### Preview Endpoints

#### Generate Preview
```http
POST /api/preview/generate
Content-Type: application/json

{
  "zpl": "^XA^FO50,50^FDTest^FS^XZ",  // OR
  "template": "example.zpl.j2",
  "variables": {"order_number": "12345"},
  "label_size": "4x6",
  "dpi": 203,
  "format": "png"
}

Response:
{
  "success": true,
  "preview_url": "/api/preview/abc123.png",
  "filename": "abc123.png",
  "label_size": "4x6",
  "dpi": 203,
  "format": "png"
}
```

#### Get Preview
```http
GET /api/preview/<filename>

Response: PNG or PDF file
```

#### Delete Preview
```http
DELETE /api/preview/<filename>

Response:
{
  "success": true,
  "message": "Preview deleted successfully",
  "filename": "abc123.png"
}
```

#### Cleanup Previews
```http
POST /api/preview/cleanup
Content-Type: application/json

{
  "days": 7
}

Response:
{
  "success": true,
  "files_deleted": 5,
  "errors": 0,
  "message": "Cleanup completed: 5 files deleted",
  "days": 7
}
```

### Print Endpoints

#### Complete Print Workflow
```http
POST /api/print/
Content-Type: application/json

{
  "template": "example.zpl.j2",
  "printer_id": "zebra-warehouse-01",
  "variables": {
    "order_number": "12345",
    "customer_name": "John Doe"
  },
  "quantity": 1,
  "generate_preview": true
}

Response:
{
  "success": true,
  "message": "Successfully printed 1 label(s)",
  "job_id": "uuid",
  "preview_url": "/api/preview/abc123.png",
  "preview_filename": "abc123.png",
  "printer": "Zebra ZT230 - Warehouse",
  "printer_id": "zebra-warehouse-01",
  "template": "example.zpl.j2",
  "quantity": 1,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Preview Only (No Printing)
```http
POST /api/print/preview-only
Content-Type: application/json

{
  "template": "example.zpl.j2",
  "variables": {"order_number": "12345"},
  "label_size": "4x6",
  "dpi": 203
}

Response:
{
  "success": true,
  "preview_url": "/api/preview/abc123.png",
  "filename": "abc123.png",
  "zpl": "^XA...",
  "label_size": "4x6",
  "dpi": 203
}
```

#### Validate Print Job
```http
POST /api/print/validate
Content-Type: application/json

{
  "template": "example.zpl.j2",
  "printer_id": "zebra-warehouse-01",
  "variables": {"order_number": "12345"},
  "quantity": 1
}

Response:
{
  "success": true,
  "valid": true,
  "message": "Print job is valid",
  "template": {...},
  "printer": {...},
  "quantity": 1
}
```

## Labelary API Integration

### API Details
- **Base URL**: `http://api.labelary.com/v1/printers/{dpi}dpi/labels/{width}x{height}/0/`
- **Method**: POST (for PNG), GET (for PDF)
- **Content-Type**: `application/x-www-form-urlencoded`
- **Timeout**: 10 seconds

### DPI Mapping
Labelary uses different DPI values than actual printer DPI:
- 6dpi = 152 DPI printers
- 8dpi = 203 DPI printers
- 12dpi = 300 DPI printers
- 24dpi = 600 DPI printers

### Supported Label Sizes
Any width x height in inches (e.g., 4x6, 4x2, 2x1, 4.5x2.5)

### Error Handling
- Network errors (503) - Graceful degradation, offline mode
- API errors (503) - Logged but don't fail print jobs
- Invalid parameters (400) - Validation errors returned
- Timeouts - 10 second timeout with retry logic

## Preview Caching Strategy

### Storage
- Directory: `previews/`
- Filename format: `{uuid}.{format}` (e.g., `abc123.png`)
- Automatic directory creation on app startup

### Cleanup
- Default retention: 7 days
- Manual cleanup via API: `POST /api/preview/cleanup`
- Automatic cleanup can be scheduled (future enhancement)

### Benefits
- Reduces Labelary API calls
- Faster preview retrieval
- Offline preview access for recent jobs
- Reduced bandwidth usage

## Integration Points

### Template Manager
- Uses `TemplateManager.render_template()` for ZPL generation
- Extracts label size from template metadata
- Validates template existence before preview

### Printer Manager
- Uses printer DPI for preview generation
- Validates printer compatibility
- Sends ZPL to printer after preview

### Print Job
- Optional preview generation during print workflow
- Preview URL included in job results
- Preview filename stored in job data

## Error Handling

### Preview Generation Errors
- **Labelary API unavailable** (503): Offline mode, print continues
- **Invalid label size** (400): Validation error returned
- **Invalid DPI** (400): Validation error returned
- **Network timeout** (503): Graceful degradation
- **File system errors** (500): Logged and reported

### Print Workflow Errors
- **Template not found** (404): Clear error message
- **Printer not found** (404): Clear error message
- **Printer disabled** (400): Clear error message
- **Incompatible label size** (400): Validation error
- **Rendering errors** (400): Template error details
- **Print errors** (500): Printer communication errors

## Testing

### Syntax Validation
All files passed Python compilation:
```bash
python3 -m py_compile preview_generator.py utils/preview_utils.py \
  blueprints/preview_bp.py blueprints/print_bp.py print_job.py test_preview.py
```

### Basic Functionality Tests
- ✓ PreviewGenerator initialization
- ✓ Label size parsing
- ✓ Previews directory creation
- ✓ UUID filename generation

### Integration Tests
Run with: `python test_preview.py --all`
- Template preview generation
- Raw ZPL preview generation
- PDF generation
- Multiple label sizes
- Cleanup functionality

## Dependencies

### Required Packages (in requirements.txt)
- `Flask==3.0.0` - Web framework
- `requests==2.31.0` - HTTP client for Labelary API
- `Jinja2==3.1.2` - Template rendering
- `python-dotenv==1.0.0` - Environment configuration

### Python Standard Library
- `os` - File system operations
- `logging` - Logging functionality
- `uuid` - Unique ID generation
- `datetime` - Timestamp handling
- `pathlib` - Path operations

## Future Enhancements

### Phase 6 (History Logging)
- Store preview URLs in history
- Track preview generation success/failure
- Preview regeneration from history

### Phase 7 (Web Interface)
- Display previews in browser
- Real-time preview updates
- Preview zoom and pan
- Side-by-side template/preview view

### Additional Features
- Automatic preview cleanup scheduling
- Preview thumbnail generation
- Preview caching with Redis
- Async preview generation
- Batch preview generation
- Preview comparison tools

## Performance Considerations

### Caching
- Local file caching reduces API calls
- UUID-based filenames prevent collisions
- Cleanup prevents disk space issues

### API Usage
- 10 second timeout prevents hanging
- Graceful degradation on API failure
- Offline mode for print-only operations

### File System
- Automatic directory creation
- Safe filename handling
- Cleanup of old files

## Security Considerations

### Input Validation
- Filename sanitization (prevent directory traversal)
- Label size validation
- DPI validation
- ZPL content size limits

### File Access
- Restricted to previews directory
- No arbitrary file access
- Safe file serving with send_file()

### API Security
- No sensitive data in preview URLs
- UUID-based filenames (unpredictable)
- Cleanup of old files

## Deployment Notes

### Directory Structure
```
/home/user/Projects/WSL/app.barcodecentral/
  preview_generator.py         # NEW
  test_preview.py              # NEW
  blueprints/
    preview_bp.py              # NEW
    print_bp.py                # NEW
  utils/
    preview_utils.py           # NEW
  print_job.py                 # UPDATED
  app.py                       # UPDATED
  previews/                    # Auto-created directory
```

### Startup Requirements
1. Ensure `previews/` directory exists (auto-created)
2. Verify network access to api.labelary.com
3. Check disk space for preview storage
4. Configure cleanup schedule (optional)

### Environment Variables
No new environment variables required. Uses existing Flask configuration.

## Conclusion

The preview generation and complete printing workflow has been successfully implemented with:
- ✅ Labelary API integration for ZPL preview generation
- ✅ Local preview caching with cleanup
- ✅ Complete print workflow with optional preview
- ✅ Comprehensive error handling
- ✅ RESTful API endpoints
- ✅ Test scripts for validation
- ✅ Integration with existing template and printer systems

All code has been validated for syntax correctness and basic functionality has been tested. The system is ready for integration testing with a running Flask application and actual Labelary API calls.