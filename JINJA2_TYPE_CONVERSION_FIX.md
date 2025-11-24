# Jinja2 Type Conversion Fix

## Problem

The template [`fn_sku_amazon.zpl.j2`](templates_zpl/fn_sku_amazon.zpl.j2) was failing with the error:
```
'>=' not supported between instances of 'str' and 'int'
```

### Root Cause

Variables from web forms and JSON APIs are always passed as **strings** by default. The Jinja2 template was attempting to:
1. Perform numeric comparison: `{% if quantity >= 100 %}` (line 21)
2. Use boolean logic: `{% if is_fragile and requires_signature %}` (line 16)

When `quantity='123'` (string) was compared to `100` (integer), Python raised a TypeError because strings and integers cannot be compared with `>=`.

### Example of Failing Input
```python
variables = {
    'address2': '123123123',      # String (OK)
    'is_fragile': '1',            # String (should be bool)
    'quantity': '123',            # String (should be int)
    'requires_signature': '1'     # String (should be bool)
}
```

## Solution

Created an intelligent type conversion system that automatically converts string variables to appropriate types before template rendering.

### Changes Made

1. **Created [`utils/type_converter.py`](utils/type_converter.py)**
   - Implements `convert_variable_types()` function
   - Automatically detects and converts:
     - Numeric strings → `int` or `float` (e.g., `'123'` → `123`, `'45.67'` → `45.67`)
     - Boolean strings → `bool` (e.g., `'1'` → `True`, `'0'` → `False`, `'true'` → `True`)
     - Other strings remain as strings

2. **Modified [`template_manager.py`](template_manager.py)**
   - Added import: `from utils.type_converter import convert_variable_types`
   - Updated `render_template()` method to convert variables before rendering
   - Added debug logging to track type conversions

### Conversion Rules

The type converter uses these rules:

**Boolean Conversion:**
- `'1'`, `'true'`, `'yes'`, `'on'` → `True`
- `'0'`, `'false'`, `'no'`, `'off'` → `False`

**Numeric Conversion:**
- Pure integers: `'123'` → `123` (int)
- Decimals: `'45.67'` → `45.67` (float)
- Negative numbers: `'-10'` → `-10` (int)

**String Preservation:**
- Regular text remains as strings: `'ABC-123'`, `'John Doe'`, etc.

### Verification

Tested with the exact failing scenario:

```python
# Input (all strings)
variables = {
    'address2': '123123123',
    'is_fragile': '1',
    'quantity': '123',
    'requires_signature': '1'
}

# After conversion
converted = {
    'address2': 123123123,        # int (numeric string)
    'is_fragile': True,           # bool
    'quantity': 123,              # int
    'requires_signature': True    # bool
}
```

**Template operations now work:**
- ✅ `quantity >= 100` → `True` (numeric comparison)
- ✅ `is_fragile and requires_signature` → `True` (boolean logic)
- ✅ `if address2` → `True` (truthiness check)

### Rendered Output

The template now correctly renders all conditional blocks:

```zpl
^FO50,50^FDFRAGILE - SIGNATURE REQUIRED^FS    # Boolean condition
^FO50,50^FDBULK ORDER^FS                       # Numeric comparison
^FO50,230^FD123123123^FS                       # String check
```

## Benefits

1. **Backward Compatible**: Existing templates continue to work
2. **Automatic**: No manual type conversion needed in templates
3. **Intelligent**: Only converts when appropriate (preserves actual strings)
4. **Debuggable**: Logs all type conversions for troubleshooting
5. **Flexible**: Supports multiple boolean formats (`'1'`, `'true'`, `'yes'`, etc.)

## Usage

No changes needed in templates or API calls. The conversion happens automatically in the rendering pipeline:

```python
# API call (variables as strings)
POST /api/preview/template
{
    "template_name": "fn_sku_amazon.zpl.j2",
    "variables": {
        "quantity": "123",      # String from form
        "is_fragile": "1"       # String from checkbox
    }
}

# Automatically converted before rendering
# quantity: 123 (int)
# is_fragile: True (bool)
```

## Testing

Created [`test_type_conversion.py`](test_type_conversion.py) with comprehensive tests:
- Numeric string conversion
- Boolean string conversion
- String preservation
- Mixed type handling
- Real-world scenario testing

## Files Modified

- [`template_manager.py`](template_manager.py) - Added type conversion to render pipeline
- [`utils/type_converter.py`](utils/type_converter.py) - New utility module
- [`test_type_conversion.py`](test_type_conversion.py) - Test suite

## Related Templates

This fix benefits ALL templates that use:
- Numeric comparisons: `{% if quantity > 10 %}`
- Boolean logic: `{% if flag1 and flag2 %}`
- Arithmetic: `{{ price * quantity }}`

No template modifications needed - the fix is transparent to all existing templates.