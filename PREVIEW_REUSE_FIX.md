# Preview Reuse Regression Fix

## Problem Summary

The preview reuse feature regressed, causing:
- ❌ Two different previews generated (203 DPI and 300 DPI)
- ❌ History preview 1.5x larger than form preview
- ❌ Two Labelary API calls per print job
- ❌ Wasted API quota

## Root Cause

The frontend was tracking `currentPreviewFilename` but **NOT passing it** to the backend during form submission at [`templates/print_form.html:290`](templates/print_form.html:290).

### What Was Happening:

1. **Preview Generation** (User views form):
   - Frontend calls `/api/preview/template`
   - Preview generated at **203 DPI** (default)
   - Frontend stores: `currentPreviewFilename = 'abc123.png'`
   - ✅ First Labelary API call

2. **Print Submission** (User clicks Print):
   - Frontend sends form data WITHOUT `preview_filename`
   - Backend sees no preview provided
   - Backend generates NEW preview at **printer DPI** (e.g., 300)
   - ❌ Second Labelary API call (WASTED!)
   - Result: Two different sized previews

## The Fix

### Changes Made:

1. **Frontend - Form Submission** ([`templates/print_form.html:290`](templates/print_form.html:290))
   ```javascript
   const formData = {
       template: templateName,
       printer_id: printerId,
       quantity: parseInt($('#quantity').val()),
       variables: {},
       generate_preview: true,
       preview_filename: currentPreviewFilename  // ← THE FIX!
   };
   ```

2. **Frontend - Reset on "Print Another"** ([`templates/print_form.html:327`](templates/print_form.html:327))
   ```javascript
   $('#printAnotherBtn').on('click', function() {
       // ... existing code ...
       currentPreviewFilename = null;  // ← Reset for new job
   });
   ```

3. **Backend - Enhanced Logging** ([`blueprints/print_bp.py:150-180`](blueprints/print_bp.py:150-180))
   - Added diagnostic logging to track preview reuse vs regeneration
   - Logs show: "✅ REUSING existing preview" or "🔄 Generating NEW preview"

## After Fix

✅ Single preview generated and reused
✅ Consistent preview size everywhere (203 DPI)
✅ One Labelary API call per print job
✅ Preview shown = preview saved in history

## How to Verify

### In Development:
```bash
# Run the test script
python3 test_preview_reuse_fix.py
```

### In Production:
```bash
# Monitor logs for preview operations
tail -f logs/*.log | grep -i preview

# Expected output when printing:
# ✅ REUSING existing preview: abc123.png (no Labelary API call)

# NOT this (the bug):
# 🔄 Generating NEW preview at 300 DPI for 4x6 label (Labelary API call)
```

### Manual Testing:
1. Open print form
2. Select template and fill variables
3. Preview generates automatically (203 DPI)
4. Open browser console (F12)
5. Click "Print Labels"
6. Check console for: `[DEBUG] Print submission - currentPreviewFilename: abc123.png`
7. Check server logs for: `✅ REUSING existing preview`

## Files Modified

- [`templates/print_form.html`](templates/print_form.html) - Pass preview_filename, reset on "Print Another"
- [`blueprints/print_bp.py`](blueprints/print_bp.py) - Enhanced logging for debugging
- [`CURSED_KNOWLEDGE.md`](CURSED_KNOWLEDGE.md) - Documented the regression
- [`test_preview_reuse_fix.py`](test_preview_reuse_fix.py) - Verification script

## Related Documentation

- [`CURSED_KNOWLEDGE.md`](CURSED_KNOWLEDGE.md) - Full history of preview DPI issues
- [`PREVIEW_IMPLEMENTATION.md`](PREVIEW_IMPLEMENTATION.md) - Preview system architecture
- Original fix: Lines 36-46 in CURSED_KNOWLEDGE.md

## Prevention

To prevent this regression in the future:

1. **Always pass `preview_filename`** when submitting print jobs if a preview was already generated
2. **Reset `currentPreviewFilename`** when starting a new print job
3. **Monitor logs** for "Generating NEW preview" messages - should only happen when no preview exists
4. **Check API quota** - sudden increase in Labelary calls indicates regression

## Impact

- **Before Fix**: 2 API calls per print job = 2,500 print jobs per day (5,000 API limit)
- **After Fix**: 1 API call per print job = 5,000 print jobs per day
- **Savings**: 50% reduction in API usage, 2x capacity increase