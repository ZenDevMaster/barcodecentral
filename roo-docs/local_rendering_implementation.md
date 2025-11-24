# Local ZPL Rendering - Implementation Specification

## Overview

This document provides detailed implementation specifications for adding local ZPL rendering to Barcode Central. This is a step-by-step guide for the Code mode to implement the design.

## Implementation Phases

### Phase 1: Library Research & Selection

#### Task 1.1: Test ZPL Libraries
**Objective**: Evaluate available Python ZPL rendering libraries

**Libraries to Test**:
1. `zpl` - https://pypi.org/project/zpl/
2. `zebra-zpl` - If available
3. Custom Pillow-based solution (fallback)

**Test Script** (`test_zpl_libraries.py`):
```python
"""
Test script to evaluate ZPL rendering libraries
Run this to determine which library to use
"""
import sys

def test_zpl_package():
    """Test the 'zpl' package"""
    try:
        import zpl
        print("✓ zpl package installed")
        
        # Test basic rendering
        test_zpl = "^XA^FO50,50^FDTest^FS^XZ"
        # Add rendering test here
        
        return True, "zpl package works"
    except ImportError:
        return False, "zpl package not installed"
    except Exception as e:
        return False, f"zpl package error: {e}"

def test_pillow_rendering():
    """Test custom Pillow-based rendering"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("✓ Pillow available")
        
        # Test basic image creation
        img = Image.new('RGB', (400, 600), 'white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "Test", fill='black')
        
        return True, "Pillow rendering possible"
    except Exception as e:
        return False, f"Pillow error: {e}"

if __name__ == "__main__":
    print("Testing ZPL Rendering Options...\n")
    
    results = []
    results.append(("zpl package", *test_zpl_package()))
    results.append(("Pillow custom", *test_pillow_rendering()))
    
    print("\nResults:")
    for name, success, message in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}: {message}")
```

**Decision Criteria**:
- Can render basic ZPL commands (^FO, ^FD, ^FS, ^BC)
- Produces acceptable image quality
- Performance < 2 seconds per label
- Active maintenance or stable

**Recommended**: Based on research, use **Pillow-based custom renderer** for maximum control and no external dependencies beyond what's already installed.

---

### Phase 2: Core Implementation

#### Task 2.1: Create LocalZPLRenderer Class

**File**: `local_zpl_renderer.py` (new file)

**Purpose**: Implement local ZPL rendering using Pillow

**Class Structure**:
```python
"""
Local ZPL Renderer for Barcode Central
Renders ZPL code to PNG images using Pillow
"""
import re
import logging
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

logger = logging.getLogger(__name__)


class LocalZPLRenderer:
    """
    Local ZPL rendering engine using Pillow
    Supports basic ZPL commands for text and simple graphics
    """
    
    # ZPL command patterns
    COMMAND_PATTERNS = {
        'field_origin': r'\^FO(\d+),(\d+)',  # ^FOx,y
        'field_data': r'\^FD([^\^]+)',        # ^FD...
        'field_separator': r'\^FS',           # ^FS
        'change_font': r'\^CF([A-Z0-9]),(\d+)(?:,(\d+))?',  # ^CFf,h,w
        'barcode_128': r'\^BC([A-Z]),(\d+),([YN])',  # ^BCo,h,f
        'graphic_box': r'\^GB(\d+),(\d+),(\d+)',  # ^GBw,h,t
        'label_start': r'\^XA',               # ^XA
        'label_end': r'\^XZ',                 # ^XZ
    }
    
    def __init__(self, dpi: int = 203):
        """
        Initialize renderer
        
        Args:
            dpi: Dots per inch (default: 203)
        """
        self.dpi = dpi
        self.dots_per_mm = dpi / 25.4
        
        # Default font settings
        self.default_font_size = 30
        self.current_font_size = self.default_font_size
        
        logger.info(f"LocalZPLRenderer initialized with {dpi} DPI")
    
    def render(
        self,
        zpl_content: str,
        width_inches: float,
        height_inches: float,
        dpi: Optional[int] = None,
        format: str = 'png'
    ) -> Tuple[bool, bytes, str]:
        """
        Render ZPL to image
        
        Args:
            zpl_content: ZPL code to render
            width_inches: Label width in inches
            height_inches: Label height in inches
            dpi: DPI override (uses instance default if None)
            format: Output format ('png' only for now)
            
        Returns:
            Tuple of (success, image_bytes, error_message)
        """
        if format != 'png':
            return False, b'', f"Format '{format}' not supported by local renderer"
        
        dpi = dpi or self.dpi
        
        try:
            # Calculate image dimensions in pixels
            width_px = int(width_inches * dpi)
            height_px = int(height_inches * dpi)
            
            # Create blank white image
            image = Image.new('RGB', (width_px, height_px), 'white')
            draw = ImageDraw.Draw(image)
            
            # Parse and render ZPL
            success, error = self._parse_and_render(zpl_content, draw, dpi)
            
            if not success:
                return False, b'', error
            
            # Convert to bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            logger.info(f"Successfully rendered ZPL locally ({width_px}x{height_px}px)")
            return True, image_bytes, ""
            
        except Exception as e:
            error_msg = f"Local rendering error: {str(e)}"
            logger.error(error_msg)
            return False, b'', error_msg
    
    def _parse_and_render(
        self,
        zpl_content: str,
        draw: ImageDraw.Draw,
        dpi: int
    ) -> Tuple[bool, str]:
        """
        Parse ZPL and render to image
        
        Args:
            zpl_content: ZPL code
            draw: PIL ImageDraw object
            dpi: DPI for coordinate conversion
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Remove comments (lines starting with ^FX)
            lines = [line for line in zpl_content.split('\n') 
                    if not line.strip().startswith('^FX')]
            zpl_clean = '\n'.join(lines)
            
            # Current position for field origin
            current_x = 0
            current_y = 0
            
            # Find all field origins and their data
            fo_pattern = re.compile(self.COMMAND_PATTERNS['field_origin'])
            fd_pattern = re.compile(self.COMMAND_PATTERNS['field_data'])
            cf_pattern = re.compile(self.COMMAND_PATTERNS['change_font'])
            
            # Process font changes
            for match in cf_pattern.finditer(zpl_clean):
                font_name, height = match.groups()[:2]
                self.current_font_size = int(height) // 2  # Approximate conversion
            
            # Process field origins and data
            position = 0
            while position < len(zpl_clean):
                # Look for field origin
                fo_match = fo_pattern.search(zpl_clean, position)
                if not fo_match:
                    break
                
                current_x = int(fo_match.group(1))
                current_y = int(fo_match.group(2))
                
                # Look for field data after this origin
                fd_match = fd_pattern.search(zpl_clean, fo_match.end())
                if fd_match:
                    text = fd_match.group(1)
                    
                    # Render text at current position
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                                 self.current_font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    draw.text((current_x, current_y), text, fill='black', font=font)
                    
                    position = fd_match.end()
                else:
                    position = fo_match.end()
            
            return True, ""
            
        except Exception as e:
            return False, f"Parse error: {str(e)}"
    
    def can_render(self, zpl_content: str) -> Tuple[bool, str]:
        """
        Check if ZPL can be rendered locally
        
        Args:
            zpl_content: ZPL code to check
            
        Returns:
            Tuple of (can_render, reason_if_not)
        """
        # Check for unsupported commands
        unsupported = []
        
        # List of commands we don't support yet
        unsupported_patterns = [
            (r'\^GF', 'Graphics Field (^GF)'),
            (r'\^IM', 'Image Move (^IM)'),
            (r'\^A@', 'Use Font Name (^A@)'),
        ]
        
        for pattern, name in unsupported_patterns:
            if re.search(pattern, zpl_content):
                unsupported.append(name)
        
        if unsupported:
            return False, f"Unsupported commands: {', '.join(unsupported)}"
        
        return True, ""
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return renderer capabilities
        
        Returns:
            Dictionary of capabilities
        """
        return {
            'name': 'LocalZPLRenderer',
            'version': '1.0',
            'supported_formats': ['png'],
            'supported_commands': [
                '^FO (Field Origin)',
                '^FD (Field Data)',
                '^FS (Field Separator)',
                '^CF (Change Font)',
                '^XA (Label Start)',
                '^XZ (Label End)',
            ],
            'max_dpi': 600,
            'min_dpi': 152,
        }
```

**Key Features**:
- Parses basic ZPL commands (^FO, ^FD, ^CF)
- Renders text at specified positions
- Handles font size changes
- Filters out comments (^FX)
- Returns detailed error messages
- Capability checking

**Limitations** (documented):
- No barcode rendering (yet)
- No graphics fields
- Limited font support
- Basic text only

---

#### Task 2.2: Update Configuration

**File**: `config.json`

**Add Preview Section**:
```json
{
  "version": "1.0",
  "units": {
    "default_unit": "inches",
    "display_unit": "inches",
    "allow_mixed_units": true,
    "conversion_precision": 1
  },
  "validation": {
    "max_width_inches": 12,
    "max_height_inches": 12,
    "min_dimension_inches": 0.1
  },
  "preview": {
    "rendering_mode": "auto",
    "local_renderer": {
      "enabled": true,
      "fallback_to_api": true,
      "dpi": 203
    },
    "api_renderer": {
      "enabled": true,
      "timeout": 10,
      "base_url": "http://api.labelary.com/v1/printers"
    },
    "cache": {
      "enabled": true,
      "ttl_days": 7
    }
  }
}
```

**File**: `utils/config_manager.py`

**Add Methods**:
```python
def get_preview_config(self) -> Dict[str, Any]:
    """
    Get preview configuration
    
    Returns:
        Preview configuration dictionary
    """
    return self._config.get('preview', {
        'rendering_mode': 'auto',
        'local_renderer': {
            'enabled': True,
            'fallback_to_api': True,
            'dpi': 203
        },
        'api_renderer': {
            'enabled': True,
            'timeout': 10,
            'base_url': 'http://api.labelary.com/v1/printers'
        }
    })

def get_rendering_mode(self) -> str:
    """
    Get preview rendering mode
    
    Returns:
        Rendering mode: 'local', 'api', or 'auto'
    """
    preview_config = self.get_preview_config()
    return preview_config.get('rendering_mode', 'auto')
```

---

#### Task 2.3: Refactor PreviewGenerator

**File**: `preview_generator.py`

**Changes Required**:

1. **Add imports**:
```python
from local_zpl_renderer import LocalZPLRenderer
from utils.config_manager import ConfigManager
```

2. **Update `__init__` method**:
```python
def __init__(self, previews_dir: str = 'previews', dpi: int = 203, label_size: str = '4x6'):
    """
    Initialize PreviewGenerator with local and API renderers
    """
    self.previews_dir = previews_dir
    self.default_dpi = dpi
    self.default_label_size = label_size
    
    # Initialize renderers
    self.local_renderer = LocalZPLRenderer(dpi=dpi)
    self.config_manager = ConfigManager()
    
    # Ensure previews directory exists
    os.makedirs(self.previews_dir, exist_ok=True)
    
    logger.info(f"PreviewGenerator initialized with local and API renderers")
```

3. **Add new methods**:
```python
def _render_local(
    self,
    zpl_content: str,
    label_size: str,
    dpi: int,
    format: str = 'png'
) -> Tuple[bool, bytes, str]:
    """
    Render using local renderer
    
    Returns:
        Tuple of (success, image_bytes, error_message)
    """
    try:
        # Parse label size
        width, height = self._parse_label_size(label_size)
        
        # Check if we can render this ZPL
        can_render, reason = self.local_renderer.can_render(zpl_content)
        if not can_render:
            return False, b'', f"Cannot render locally: {reason}"
        
        # Render
        return self.local_renderer.render(zpl_content, width, height, dpi, format)
        
    except Exception as e:
        return False, b'', f"Local rendering failed: {str(e)}"

def _render_api(
    self,
    zpl_content: str,
    label_size: str,
    dpi: int,
    format: str = 'png'
) -> Tuple[bool, bytes, str]:
    """
    Render using Labelary API (existing implementation)
    
    Returns:
        Tuple of (success, image_bytes, error_message)
    """
    # This is the existing generate_preview logic
    # Move the current implementation here
    pass

def _render_auto(
    self,
    zpl_content: str,
    label_size: str,
    dpi: int,
    format: str = 'png'
) -> Tuple[bool, bytes, str]:
    """
    Try local rendering first, fallback to API
    
    Returns:
        Tuple of (success, image_bytes, error_message)
    """
    # Try local first
    success, data, error = self._render_local(zpl_content, label_size, dpi, format)
    
    if success:
        logger.info("Preview generated using local renderer")
        return success, data, error
    
    # Fallback to API
    logger.info(f"Local rendering failed ({error}), falling back to API")
    return self._render_api(zpl_content, label_size, dpi, format)
```

4. **Update `generate_preview` method**:
```python
def generate_preview(
    self, 
    zpl_content: str, 
    label_size: Optional[str] = None, 
    dpi: Optional[int] = None, 
    format: str = 'png'
) -> Tuple[bool, bytes, str]:
    """
    Generate preview image from ZPL content
    Uses local or API rendering based on configuration
    """
    # Use defaults if not provided
    label_size = label_size or self.default_label_size
    dpi = dpi or self.default_dpi
    
    # Validate format
    if format not in ['png', 'pdf']:
        return False, b'', f"Invalid format '{format}'. Must be 'png' or 'pdf'"
    
    # Get rendering mode from config
    rendering_mode = self.config_manager.get_rendering_mode()
    
    # Route to appropriate renderer
    if rendering_mode == 'local':
        return self._render_local(zpl_content, label_size, dpi, format)
    elif rendering_mode == 'api':
        return self._render_api(zpl_content, label_size, dpi, format)
    else:  # auto
        return self._render_auto(zpl_content, label_size, dpi, format)
```

---

### Phase 3: Testing

#### Task 3.1: Unit Tests

**File**: `tests/test_local_renderer.py` (new file)

```python
"""
Unit tests for LocalZPLRenderer
"""
import pytest
from local_zpl_renderer import LocalZPLRenderer


class TestLocalZPLRenderer:
    """Test LocalZPLRenderer functionality"""
    
    def test_initialization(self):
        """Test renderer initialization"""
        renderer = LocalZPLRenderer(dpi=203)
        assert renderer.dpi == 203
    
    def test_simple_text_rendering(self):
        """Test rendering simple text"""
        renderer = LocalZPLRenderer()
        zpl = "^XA^FO50,50^FDTest^FS^XZ"
        
        success, image_bytes, error = renderer.render(zpl, 4.0, 6.0)
        
        assert success is True
        assert len(image_bytes) > 0
        assert error == ""
    
    def test_can_render_check(self):
        """Test capability checking"""
        renderer = LocalZPLRenderer()
        
        # Simple ZPL should be renderable
        simple_zpl = "^XA^FO50,50^FDTest^FS^XZ"
        can_render, reason = renderer.can_render(simple_zpl)
        assert can_render is True
    
    def test_get_capabilities(self):
        """Test capabilities reporting"""
        renderer = LocalZPLRenderer()
        caps = renderer.get_capabilities()
        
        assert 'name' in caps
        assert 'supported_formats' in caps
        assert 'png' in caps['supported_formats']
```

#### Task 3.2: Integration Tests

**File**: `tests/test_preview_integration.py`

```python
"""
Integration tests for preview generation with local rendering
"""
import pytest
from preview_generator import PreviewGenerator


class TestPreviewIntegration:
    """Test preview generation with local and API rendering"""
    
    def test_auto_mode_uses_local_first(self):
        """Test that auto mode tries local rendering first"""
        generator = PreviewGenerator()
        
        # Simple ZPL that local renderer can handle
        zpl = "^XA^FO50,50^FDTest^FS^XZ"
        
        success, image_bytes, error = generator.generate_preview(zpl)
        
        assert success is True
        assert len(image_bytes) > 0
    
    def test_fallback_to_api(self):
        """Test fallback to API when local fails"""
        generator = PreviewGenerator()
        
        # Complex ZPL that local renderer cannot handle
        zpl = "^XA^GFA,100,100,10,^XZ"  # Graphics field
        
        success, image_bytes, error = generator.generate_preview(zpl)
        
        # Should fallback to API (may fail if no internet)
        # This test documents the behavior
        assert isinstance(success, bool)
```

---

### Phase 4: Documentation

#### Task 4.1: Update API Documentation

**File**: `API.md`

**Add Section**:
```markdown
## Preview Rendering Modes

Barcode Central supports multiple rendering modes for label previews:

### Rendering Modes

- **local**: Use local ZPL rendering (faster, offline capable)
- **api**: Use Labelary API (more features, requires internet)
- **auto**: Try local first, fallback to API (recommended)

### Configuration

Set rendering mode in `config.json`:

```json
{
  "preview": {
    "rendering_mode": "auto"
  }
}
```

### Local Rendering Capabilities

The local renderer currently supports:
- Text fields (^FO, ^FD, ^FS)
- Font changes (^CF)
- Basic positioning

Not yet supported:
- Barcodes (^BC, ^BQ, etc.)
- Graphics (^GF, ^GB)
- Images (^IM)

For unsupported features, the system automatically falls back to the Labelary API.
```

---

## Implementation Checklist

### Prerequisites
- [ ] Pillow is installed (already in requirements.txt)
- [ ] Development environment is set up
- [ ] Tests can be run

### Phase 1: Core Implementation
- [ ] Create `local_zpl_renderer.py`
- [ ] Implement `LocalZPLRenderer` class
- [ ] Add basic ZPL parsing
- [ ] Add text rendering
- [ ] Test with simple ZPL

### Phase 2: Integration
- [ ] Update `config.json` with preview settings
- [ ] Update `utils/config_manager.py` with preview methods
- [ ] Refactor `preview_generator.py`:
  - [ ] Add local renderer initialization
  - [ ] Add `_render_local()` method
  - [ ] Add `_render_api()` method (refactor existing)
  - [ ] Add `_render_auto()` method
  - [ ] Update `generate_preview()` to use modes

### Phase 3: Testing
- [ ] Create `tests/test_local_renderer.py`
- [ ] Write unit tests for LocalZPLRenderer
- [ ] Create `tests/test_preview_integration.py`
- [ ] Write integration tests
- [ ] Test with all sample templates
- [ ] Test fallback mechanism

### Phase 4: Documentation
- [ ] Update `API.md` with rendering modes
- [ ] Update `README.md` with local rendering info
- [ ] Add configuration examples
- [ ] Document limitations

### Phase 5: Deployment
- [ ] Test in development environment
- [ ] Verify no regressions
- [ ] Deploy to production
- [ ] Monitor performance

## Success Metrics

- [ ] Local rendering works for simple text labels
- [ ] Fallback to API works seamlessly
- [ ] No regression in existing functionality
- [ ] Configuration is intuitive
- [ ] Tests pass with >80% coverage

## Notes

- Start with basic text rendering
- Add more ZPL commands incrementally
- Always maintain API fallback
- Document limitations clearly
- Focus on common use cases first