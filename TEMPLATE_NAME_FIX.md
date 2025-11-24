# Template Name Input Fix

## Problem
The template creation form required users to enter filenames with `.zpl.j2` extension and underscores (e.g., `product_label_4x2.zpl.j2`) in the "Template Name" field, which was confusing since the metadata stored in the file used friendly display names (e.g., "Product Label 4x2").

## Solution
Separated the concept of **display name** (user-friendly) from **filename** (system-generated):

### Changes Made

#### 1. Added Filename Generation Function (`utils/validators.py`)
- New function: `generate_template_filename(display_name: str) -> str`
- Converts friendly names like "Product Label 4x2" to safe filenames like "product_label_4x2.zpl.j2"
- Handles special characters, spaces, and ensures proper `.zpl.j2` extension

#### 2. Updated Backend (`blueprints/templates_bp.py`)
- Modified template creation endpoint to:
  - Accept display name in the `name` field
  - Auto-generate filename from display name
  - Store display name in template metadata
  - Support legacy `filename` parameter for backward compatibility

#### 3. Improved Dimension Parsing (`blueprints/templates_bp.py`)
- Fixed parsing of individual dimension fields with units (e.g., "50mm", "15mm")
- Added support for:
  - Millimeters: `50mm`
  - Centimeters: `10cm`
  - Inches (explicit): `4in` or `4inches`
  - Inches (implicit): `4`
- Converts all units to inches for storage

#### 4. Updated Frontend (`templates/new_template.html`)
- Changed placeholder from `"e.g., product_label"` to `"e.g., Product Label 4x2"`
- Updated help text to: "Enter a friendly name - filename will be generated automatically"

### Examples

**Display Name → Generated Filename:**
- "Product Label 4x2" → `product_label_4x2.zpl.j2`
- "Shipping Label" → `shipping_label.zpl.j2`
- "My Custom Label!!!" → `my_custom_label.zpl.j2`

**Dimension Parsing:**
- `50mm x 15mm` → `2.0x0.6` inches
- `10cm x 15cm` → `3.9x5.9` inches
- `4 x 6` → `4.0x6.0` inches

### Backward Compatibility
- Legacy API calls with explicit `filename` parameter still work
- Existing templates are unaffected
- Metadata format remains the same

### Testing
Run the application and create a new template:
1. Enter a friendly name like "Product Label 4x2"
2. Enter dimensions with units like "50mm" and "15mm"
3. The system will automatically generate `product_label_4x2.zpl.j2`
4. The metadata will store the friendly name "Product Label 4x2"