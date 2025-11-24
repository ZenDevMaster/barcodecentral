# Reprint Functionality Implementation

## Overview

The reprint functionality allows users to quickly reprint labels from the History page with all original settings pre-populated, while still allowing modifications before printing.

## Implementation Details

### Architecture

**Session Storage Approach**
- Uses browser `sessionStorage` to transfer data between History and Print Form pages
- No URL length limitations
- Clean URLs without query parameters
- Data automatically cleared after use

### Files Modified

#### 1. `templates/history.html`

**Changes to Reprint Button:**
```html
<button class="btn btn-outline-success reprint-job" 
        data-template="{{ item.template }}"
        data-template-name="{{ item.template_name }}"
        data-printer-id="{{ item.printer_id }}"
        data-printer-name="{{ item.printer_name }}"
        data-variables="{{ item.variables|tojson|escape }}"
        data-quantity="{{ item.quantity|default(1) }}"
        data-bs-toggle="tooltip" title="Reprint">
    <i class="bi bi-arrow-repeat"></i>
</button>
```

**JavaScript Handler:**
```javascript
$('.reprint-job').on('click', function() {
    const reprintData = {
        template: $(this).data('template'),
        templateName: $(this).data('template-name'),
        printerId: $(this).data('printer-id'),
        printerName: $(this).data('printer-name'),
        variables: $(this).data('variables'),
        quantity: $(this).data('quantity')
    };
    
    sessionStorage.setItem('reprintData', JSON.stringify(reprintData));
    window.location.href = '/print';
});
```

#### 2. `templates/print_form.html`

**Auto-Population Logic:**
```javascript
const reprintDataStr = sessionStorage.getItem('reprintData');
if (reprintDataStr) {
    const reprintData = JSON.parse(reprintDataStr);
    
    // Clear immediately to prevent reuse
    sessionStorage.removeItem('reprintData');
    
    // Auto-select template
    $('#templateSelect').val(reprintData.template).trigger('change');
    
    // Wait for template to load, then populate fields
    setTimeout(() => {
        // Auto-select printer
        $('#printerSelect').val(reprintData.printerId);
        
        // Auto-populate quantity
        $('#quantity').val(reprintData.quantity);
        
        // Auto-populate variables
        Object.keys(reprintData.variables).forEach(varName => {
            $(`#var_${varName}`).val(reprintData.variables[varName]);
        });
        
        // Auto-generate preview
        setTimeout(() => generatePreview(), 300);
    }, 800);
}
```

## Features

### ✅ Complete Data Transfer
- Template filename and display name
- Printer ID and display name
- All variable values
- Print quantity

### ✅ User Experience
- **Clean URLs**: No query parameters (just `/print`)
- **Auto-Population**: All fields filled automatically
- **Auto-Preview**: Preview generated automatically
- **Fully Editable**: User can modify any field before printing
- **Fast**: No server round-trip needed

### ✅ Technical Benefits
- **No URL Limits**: SessionStorage handles large data
- **Secure**: Data only in browser session
- **Self-Cleaning**: Data removed after use
- **Error Handling**: Graceful fallback on errors
- **Debug Logging**: Console logs for troubleshooting

## User Flow

1. **User clicks "Reprint" button** in History page
2. **Data stored** in sessionStorage
3. **Redirect** to `/print` page
4. **Auto-population** occurs:
   - Template selected
   - Printer selected
   - Variables filled
   - Quantity set
5. **Preview generated** automatically
6. **User can modify** any field if needed
7. **User clicks "Print Labels"** to complete reprint
8. **SessionStorage cleaned** automatically

## Data Structure

### SessionStorage Key: `reprintData`

```json
{
  "template": "example.zpl.j2",
  "templateName": "Example Label",
  "printerId": "zebra-warehouse-01",
  "printerName": "Zebra ZT230 - Warehouse",
  "variables": {
    "order_number": "12345",
    "customer_name": "John Doe",
    "address": "123 Main St"
  },
  "quantity": 5
}
```

## Testing

### Manual Testing Steps

1. Navigate to History page
2. Find a successful print job
3. Click the "Reprint" button (↻ icon)
4. Verify redirect to `/print` (clean URL)
5. Verify template is auto-selected
6. Verify printer is auto-selected
7. Verify all variables are populated
8. Verify quantity is set
9. Verify preview is generated
10. Modify a field and verify it updates
11. Click "Print Labels" to complete

### Automated Test

Run: `python3 test_reprint_functionality.py`

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ All modern browsers with sessionStorage support

## Troubleshooting

### Issue: Fields not populating

**Check:**
1. Open browser console (F12)
2. Look for `[REPRINT]` log messages
3. Verify sessionStorage has data before redirect
4. Check timing delays (may need adjustment)

### Issue: Preview not generating

**Check:**
1. Verify all variables are populated
2. Check console for preview generation errors
3. Ensure template is valid

### Issue: Wrong printer selected

**Check:**
1. Verify `printer_id` in history matches printer in `printers.json`
2. Check if printer still exists and is enabled

## Future Enhancements

### Possible Additions:

1. **Reprint Mode Toggle**
   - Option to use exact original ZPL vs. re-render with current template
   - Useful if template has been modified since original print

2. **Bulk Reprint**
   - Select multiple history entries
   - Reprint all with one click

3. **Reprint with Modifications**
   - Quick edit modal before reprinting
   - Batch variable updates

4. **Reprint History**
   - Track which jobs are reprints
   - Link reprints to original jobs

## Related Files

- `templates/history.html` - History page with reprint button
- `templates/print_form.html` - Print form with auto-population
- `test_reprint_functionality.py` - Automated tests
- `history_manager.py` - History data management
- `print_job.py` - Print job execution

## Notes

- SessionStorage is cleared after use to prevent accidental reuse
- All fields remain editable after auto-population
- Preview is generated automatically but can be regenerated
- Original ZPL is stored in history but not currently used for reprint (uses template re-rendering)