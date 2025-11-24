# Local ZPL Rendering - Simplified Design (Local Only)

## Executive Summary

This document outlines the simplified design for implementing **local-only** ZPL rendering in Barcode Central, completely replacing the Labelary API dependency.

## Design Principles

1. **Local Only**: No external API calls, no internet dependency
2. **Offline First**: Must work completely offline
3. **Simple Architecture**: Direct replacement of Labelary API calls
4. **Pillow-Based**: Use existing Pillow dependency for rendering

## Simplified Architecture

```
User Request → PreviewGenerator → LocalZPLRenderer → PNG Output
```

**That's it!** No fallback, no mode selection, just local rendering.

## Implementation Strategy

### Phase 1: Create LocalZPLRenderer

**File**: `local_zpl_renderer.py` (new)

A simple, focused renderer that handles the most common ZPL commands used in the templates.

**Supported ZPL Commands** (Priority Order):
1. `^XA` / `^XZ` - Label start/end
2. `^FO` - Field Origin (positioning)
3. `^FD` - Field Data (text content)
4. `^FS` - Field Separator
5. `^CF` - Change Font
6. `^FX` - Comments (ignore)
7. `^BC` - Code 128 Barcode (basic implementation)
8. `^BY` - Barcode parameters

**Not Implementing** (can add later if needed):
- Graphics fields (^GF, ^GB)
- Images (^IM)
- Complex barcodes (^QR, ^BQ)
- Advanced formatting

### Phase 2: Replace PreviewGenerator Logic

**File**: `preview_generator.py`

**Changes**:
1. Remove all Labelary API code
2. Remove `requests` dependency usage
3. Replace with direct calls to `LocalZPLRenderer`
4. Simplify error handling

**Before** (current):
```python
def generate_preview(self, zpl_content, ...):
    # Build Labelary API URL
    url = f"{self.LABELARY_BASE_URL}/..."
    # Make HTTP request
    response = requests.post(url, ...)
    return response.content
```

**After** (simplified):
```python
def generate_preview(self, zpl_content, ...):
    # Parse label size
    width, height = self._parse_label_size(label_size)
    # Render locally
    return self.local_renderer.render(zpl_content, width, height, dpi)
```

### Phase 3: Update Dependencies

**File**: `requirements.txt`

**Remove**: `requests==2.31.0` (no longer needed for preview generation)

**Keep**: `Pillow==10.1.0` (already present, used for rendering)

## Detailed Implementation

### LocalZPLRenderer Class

```python
"""
Local ZPL Renderer - Simple, offline ZPL to PNG converter
"""
import re
import logging
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

logger = logging.getLogger(__name__)


class LocalZPLRenderer:
    """
    Renders ZPL code to PNG images using Pillow
    Supports common ZPL commands for text and basic barcodes
    """
    
    def __init__(self, dpi: int = 203):
        """
        Initialize renderer
        
        Args:
            dpi: Dots per inch (default: 203 for standard Zebra printers)
        """
        self.dpi = dpi
        logger.info(f"LocalZPLRenderer initialized at {dpi} DPI")
    
    def render(
        self,
        zpl_content: str,
        width_inches: float,
        height_inches: float,
        dpi: Optional[int] = None
    ) -> Tuple[bool, bytes, str]:
        """
        Render ZPL to PNG image
        
        Args:
            zpl_content: ZPL code to render
            width_inches: Label width in inches
            height_inches: Label height in inches
            dpi: DPI override (uses instance default if None)
            
        Returns:
            Tuple of (success, image_bytes, error_message)
        """
        dpi = dpi or self.dpi
        
        try:
            # Calculate pixel dimensions
            width_px = int(width_inches * dpi)
            height_px = int(height_inches * dpi)
            
            # Create blank white label
            image = Image.new('RGB', (width_px, height_px), 'white')
            draw = ImageDraw.Draw(image)
            
            # Parse and render ZPL
            self._parse_and_render(zpl_content, draw, dpi)
            
            # Convert to PNG bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            logger.info(f"Rendered ZPL to {width_px}x{height_px}px PNG ({len(image_bytes)} bytes)")
            return True, image_bytes, ""
            
        except Exception as e:
            error_msg = f"Rendering error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, b'', error_msg
    
    def _parse_and_render(self, zpl_content: str, draw: ImageDraw.Draw, dpi: int):
        """
        Parse ZPL commands and render to image
        
        Args:
            zpl_content: ZPL code
            draw: PIL ImageDraw object
            dpi: DPI for coordinate scaling
        """
        # Remove comments (^FX lines)
        lines = [line for line in zpl_content.split('\n') 
                if not line.strip().startswith('^FX')]
        zpl_clean = '\n'.join(lines)
        
        # Current state
        current_x = 0
        current_y = 0
        current_font_size = 30
        
        # Regular expressions for ZPL commands
        fo_pattern = re.compile(r'\^FO(\d+),(\d+)')  # Field Origin
        fd_pattern = re.compile(r'\^FD([^\^]+)')     # Field Data
        cf_pattern = re.compile(r'\^CF[A-Z0-9],(\d+)')  # Change Font
        bc_pattern = re.compile(r'\^BC[A-Z],(\d+)')  # Barcode Code 128
        
        # Process font changes
        for match in cf_pattern.finditer(zpl_clean):
            height = int(match.group(1))
            current_font_size = height // 2  # Approximate conversion
        
        # Process field origins and data
        position = 0
        while position < len(zpl_clean):
            # Find next field origin
            fo_match = fo_pattern.search(zpl_clean, position)
            if not fo_match:
                break
            
            current_x = int(fo_match.group(1))
            current_y = int(fo_match.group(2))
            
            # Check for barcode after this position
            bc_match = bc_pattern.search(zpl_clean, fo_match.end())
            if bc_match and bc_match.start() < fo_match.end() + 50:
                # This is a barcode field
                fd_match = fd_pattern.search(zpl_clean, bc_match.end())
                if fd_match:
                    barcode_data = fd_match.group(1)
                    barcode_height = int(bc_match.group(1))
                    self._render_barcode(draw, current_x, current_y, 
                                       barcode_data, barcode_height)
                    position = fd_match.end()
                    continue
            
            # Look for field data (text)
            fd_match = fd_pattern.search(zpl_clean, fo_match.end())
            if fd_match and fd_match.start() < fo_match.end() + 50:
                text = fd_match.group(1).strip()
                
                # Load font
                try:
                    font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        current_font_size
                    )
                except:
                    font = ImageFont.load_default()
                
                # Render text
                draw.text((current_x, current_y), text, fill='black', font=font)
                position = fd_match.end()
            else:
                position = fo_match.end()
    
    def _render_barcode(self, draw: ImageDraw.Draw, x: int, y: int, 
                       data: str, height: int):
        """
        Render a simple Code 128 barcode representation
        
        Args:
            draw: PIL ImageDraw object
            x: X position
            y: Y position
            data: Barcode data
            height: Barcode height in dots
        """
        # Simple barcode representation: alternating black/white bars
        bar_width = 3
        current_x = x
        
        # Draw bars for each character (simplified)
        for i, char in enumerate(data):
            if i % 2 == 0:
                # Black bar
                draw.rectangle(
                    [current_x, y, current_x + bar_width, y + height],
                    fill='black'
                )
            current_x += bar_width + 2
        
        # Draw text below barcode
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20
            )
        except:
            font = ImageFont.load_default()
        
        draw.text((x, y + height + 5), data, fill='black', font=font)
```

### Updated PreviewGenerator

```python
"""
Preview Generator - Simplified for local rendering only
"""
import os
import logging
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from local_zpl_renderer import LocalZPLRenderer
from utils.label_size import LabelSize

logger = logging.getLogger(__name__)


class PreviewGenerator:
    """
    Generates label previews using local ZPL rendering
    """
    
    def __init__(self, previews_dir: str = 'previews', dpi: int = 203, 
                 label_size: str = '4x6'):
        """
        Initialize PreviewGenerator
        
        Args:
            previews_dir: Directory to store preview files
            dpi: Default DPI for previews
            label_size: Default label size
        """
        self.previews_dir = previews_dir
        self.default_dpi = dpi
        self.default_label_size = label_size
        
        # Initialize local renderer
        self.renderer = LocalZPLRenderer(dpi=dpi)
        
        # Ensure previews directory exists
        os.makedirs(self.previews_dir, exist_ok=True)
        
        logger.info(f"PreviewGenerator initialized (local rendering)")
    
    def generate_preview(
        self, 
        zpl_content: str, 
        label_size: Optional[str] = None, 
        dpi: Optional[int] = None, 
        format: str = 'png'
    ) -> Tuple[bool, bytes, str]:
        """
        Generate preview image from ZPL content
        
        Args:
            zpl_content: ZPL code to render
            label_size: Label size (e.g., '4x6')
            dpi: DPI setting
            format: Output format (only 'png' supported)
            
        Returns:
            Tuple of (success, image_bytes, error_message)
        """
        # Use defaults if not provided
        label_size = label_size or self.default_label_size
        dpi = dpi or self.default_dpi
        
        # Validate format
        if format != 'png':
            return False, b'', f"Only PNG format supported (requested: {format})"
        
        # Parse label size
        try:
            width, height = self._parse_label_size(label_size)
        except ValueError as e:
            return False, b'', str(e)
        
        # Render locally
        return self.renderer.render(zpl_content, width, height, dpi)
    
    def generate_pdf(self, *args, **kwargs) -> Tuple[bool, bytes, str]:
        """PDF generation not supported in local renderer"""
        return False, b'', "PDF generation not supported by local renderer"
    
    def save_preview(
        self, 
        zpl_content: str, 
        filename: Optional[str] = None,
        label_size: Optional[str] = None, 
        dpi: Optional[int] = None, 
        format: str = 'png'
    ) -> Tuple[bool, str, str]:
        """
        Generate and save preview to file
        
        Returns:
            Tuple of (success, filename, error_message)
        """
        # Generate preview
        success, image_bytes, error_msg = self.generate_preview(
            zpl_content, label_size, dpi, format
        )
        
        if not success:
            return False, "", error_msg
        
        # Generate filename if not provided
        if not filename:
            filename = f"{uuid.uuid4()}.{format}"
        elif not filename.endswith(f'.{format}'):
            filename = f"{filename}.{format}"
        
        # Save to file
        filepath = os.path.join(self.previews_dir, filename)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"Saved preview: {filepath}")
            return True, filename, ""
            
        except Exception as e:
            error_msg = f"Error saving preview: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    # Keep existing helper methods: get_preview_path, preview_exists, 
    # cleanup_old_previews, _parse_label_size
```

## Implementation Checklist

### Step 1: Create Local Renderer
- [ ] Create `local_zpl_renderer.py`
- [ ] Implement `LocalZPLRenderer` class
- [ ] Test with simple ZPL
- [ ] Test with sample templates

### Step 2: Update PreviewGenerator
- [ ] Remove Labelary API code
- [ ] Remove `requests` import
- [ ] Add `LocalZPLRenderer` import
- [ ] Replace `generate_preview()` logic
- [ ] Update `generate_pdf()` to return not supported
- [ ] Keep helper methods unchanged

### Step 3: Update Dependencies
- [ ] Remove `requests` from `requirements.txt` (if not used elsewhere)
- [ ] Verify `Pillow` is present

### Step 4: Testing
- [ ] Test with `example.zpl.j2`
- [ ] Test with `product_label_4x2.zpl.j2`
- [ ] Test with `address_label_4x6.zpl.j2`
- [ ] Verify preview images look reasonable
- [ ] Test error handling

### Step 5: Documentation
- [ ] Update README with "offline rendering"
- [ ] Remove Labelary API references
- [ ] Document supported ZPL commands
- [ ] Add troubleshooting section

## Expected Results

### What Will Work
- ✅ Text rendering at specified positions
- ✅ Font size changes
- ✅ Basic barcode representation
- ✅ All sample templates (text-based)
- ✅ Completely offline operation
- ✅ Fast rendering (< 500ms)

### Known Limitations
- ⚠️ Barcodes are simplified (not scannable, just visual)
- ⚠️ No graphics fields support
- ⚠️ Limited font selection
- ⚠️ No PDF output

### Future Enhancements (if needed)
- Add proper barcode library for scannable codes
- Support more ZPL commands
- Add PDF generation
- Custom fonts support

## Success Criteria

1. ✅ Preview generation works offline
2. ✅ No external API dependencies
3. ✅ All sample templates render
4. ✅ Performance < 1 second per preview
5. ✅ No regression in other functionality

## Migration Notes

**Breaking Changes**:
- PDF generation no longer supported (returns error)
- Some advanced ZPL commands may not render

**Non-Breaking**:
- API endpoints remain the same
- Response format unchanged
- Existing preview files unaffected

## Timeline

- **Phase 1** (Create Renderer): 2-3 hours
- **Phase 2** (Update PreviewGenerator): 1-2 hours
- **Phase 3** (Testing): 1-2 hours
- **Phase 4** (Documentation): 1 hour

**Total**: ~6-8 hours of development time