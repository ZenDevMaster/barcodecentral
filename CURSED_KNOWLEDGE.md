# Cursed Knowledge: Things That Will Bite You

This document contains hard-won knowledge about subtle bugs, gotchas, and design decisions that aren't obvious from the code alone.

## Preview Generation DPI Mismatch (Nov 2024) - REGRESSION FIXED

### The Regression (Discovered: Nov 2024)

**Symptom**: The preview reuse feature regressed - previews were being generated twice again, even though the fix was previously implemented.

**Root Cause**: Frontend was tracking `currentPreviewFilename` but **NOT passing it** to the backend during form submission.

**Code Location**: [`templates/print_form.html:290`](templates/print_form.html:290) - Form submission was missing `preview_filename` parameter

**The Fix**:
1. Added `preview_filename: currentPreviewFilename` to form submission data
2. Added `currentPreviewFilename = null` reset on "Print Another" button
3. Added diagnostic logging to track preview reuse vs regeneration

**Files Modified**:
- [`templates/print_form.html:290`](templates/print_form.html:290) - Pass preview_filename in form data
- [`templates/print_form.html:327`](templates/print_form.html:327) - Reset preview filename on "Print Another"
- [`blueprints/print_bp.py:150-180`](blueprints/print_bp.py:150-180) - Enhanced logging for preview reuse tracking

### The Original Problem (Fixed Previously)

**Symptom**: Two different preview images were being generated for the same label - one displayed correctly on the print form, another (1.5x larger) saved in history.

**Root Cause**: The system was generating previews **twice** with **different DPI settings**:

1. **Form Preview** (`/api/preview/template`):
   - Generated when user views print form
   - Used default DPI: **203**
   - Example: 466x243 pixels for 2.3x1.2" label

2. **Print Preview** (`/api/print/`):
   - Generated during print job execution  
   - Used printer's configured DPI: **300** (or whatever the printer was set to)
   - Example: 699x364 pixels for same 2.3x1.2" label (1.5x larger!)

### Why It Happened

The print endpoint code at [`blueprints/print_bp.py:150`](blueprints/print_bp.py:150):
```python
dpi = data.get('dpi') or printer.get('dpi', 203)
```

This pulled the DPI from the printer configuration, which could be different from the preview form's default.

### The Fix

**Solution**: Preview reuse pattern - generate once, use everywhere.

Modified [`blueprints/print_bp.py`](blueprints/print_bp.py:72) to:
1. Accept `preview_filename` parameter from frontend
2. Check if preview file exists
3. Reuse existing preview if available
4. Only generate new preview if none provided

Modified [`templates/print_form.html`](templates/print_form.html:160) to:
1. Track `currentPreviewFilename` when preview is generated
2. Pass it to print endpoint in form submission
3. Reset on "Print Another"

### Lessons Learned

1. **Single Source of Truth**: Don't generate the same thing twice with different parameters
2. **DPI Consistency**: Preview DPI should match what user sees, not what printer is configured for
3. **Reuse Over Regenerate**: If you already have a preview, use it
4. **Log Everything**: The issue was found by examining Labelary API URLs in logs

### How to Verify the Fix

```bash
# Check logs for preview generation
tail -f logs/*.log | grep -i "preview\|labelary"

# Should see:
# - One preview generation per print job
# - "Reusing existing preview" message
# - Same DPI value for both preview and print
```

### Related Files

- [`blueprints/print_bp.py`](blueprints/print_bp.py:144-185) - Preview reuse logic
- [`templates/print_form.html`](templates/print_form.html:160) - Preview filename tracking
- [`preview_generator.py`](preview_generator.py:44) - Preview generation with Labelary API

---

## Labelary API Integration (Nov 2024)

### PNG DPI Metadata Issue

**Problem**: Labelary returns PNG files without DPI metadata (no pHYs chunk). Image viewers default to 72 or 96 DPI, making labels appear 2-3x larger than intended.

**Solution**: Add pHYs chunk directly to PNG bytes without re-encoding the image. See [`preview_generator.py:331`](preview_generator.py:331) - `_add_png_dpi_metadata()` method.

**Why Not Use Pillow**: Pillow's `img.save(dpi=...)` re-encodes the image and can change dimensions. Direct chunk manipulation preserves exact pixels from Labelary.

### Labelary URL Format

Correct format: `http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{width}x{height}/0/`

- Use `dpmm` (dots per millimeter) not `dpi` in URL
- DPI to dpmm mapping:
  - 152 DPI = 6 dpmm
  - 203 DPI = 8 dpmm  
  - 300 DPI = 12 dpmm
  - 600 DPI = 24 dpmm

### Rate Limits

- 5000 free renders per day
- No authentication required
- Resets daily at midnight UTC

---

## Future Gotchas to Watch For

### Preview Caching

If you implement preview caching, remember:
- Cache key must include DPI and label size
- Don't cache by template name alone
- Clear cache when template is modified

### Printer DPI Configuration

Different printers may have different DPI settings. Always:
- Use preview DPI consistently
- Document which DPI is used for what
- Consider making DPI visible in UI

### History Preview Display

History entries reference preview files by filename. If you:
- Delete old previews (cleanup job)
- Change preview naming scheme
- Move preview directory

Then history entries will show broken images. Consider:
- Keeping previews referenced in recent history
- Implementing preview regeneration from ZPL in history
- Adding preview expiration metadata

---

## How to Add to This Document

When you discover a subtle bug or gotcha:

1. **Document the symptom** - What did users see?
2. **Explain the root cause** - Why did it happen?
3. **Describe the fix** - How was it solved?
4. **Add lessons learned** - What should future developers know?
5. **Link to relevant code** - Make it easy to find

Remember: If it took you more than 30 minutes to debug, it belongs here.