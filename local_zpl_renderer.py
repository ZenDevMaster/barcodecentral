"""
Local ZPL Renderer for Barcode Central
CURRENTLY UNUSED - Preserved for potential future offline fallback

This module was previously used for offline preview generation but has been
replaced with Labelary API integration for better quality and full ZPL support.

Limitations of this local renderer:
- Barcodes are visual representations only (not scannable)
- Limited ZPL command support (text, basic positioning, simple barcodes only)
- No PDF generation
- No graphics/image support (^GF, ^GB, ^IM)
- Limited font selection

The system now uses Labelary API (http://api.labelary.com) which provides:
- Full ZPL command support
- Scannable barcodes
- Both PNG and PDF output
- Professional quality rendering
- 5000 free renders per day

This code is kept in the codebase for potential future use as an offline fallback
if Labelary API becomes unavailable.
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
    No external API dependencies - works completely offline
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
            
            logger.debug(f"Rendering ZPL to {width_px}x{height_px}px at {dpi} DPI")
            
            # Create blank white label
            image = Image.new('RGB', (width_px, height_px), 'white')
            draw = ImageDraw.Draw(image)
            
            # Parse and render ZPL
            self._parse_and_render(zpl_content, draw, dpi)
            
            # Convert to PNG bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            logger.info(f"Successfully rendered ZPL to PNG ({len(image_bytes)} bytes)")
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
        bc_pattern = re.compile(r'\^BC([A-Z]),(\d+)')  # Barcode Code 128
        by_pattern = re.compile(r'\^BY(\d+)')  # Barcode module width
        
        # Process font changes globally
        for match in cf_pattern.finditer(zpl_clean):
            height = int(match.group(1))
            current_font_size = height // 2  # Approximate conversion from ZPL to points
            logger.debug(f"Font size changed to {current_font_size}pt")
        
        # Process field origins and data
        position = 0
        barcode_width = 3  # Default barcode module width
        
        # Check for barcode width setting
        by_match = by_pattern.search(zpl_clean)
        if by_match:
            barcode_width = int(by_match.group(1))
        
        while position < len(zpl_clean):
            # Find next field origin
            fo_match = fo_pattern.search(zpl_clean, position)
            if not fo_match:
                break
            
            current_x = int(fo_match.group(1))
            current_y = int(fo_match.group(2))
            
            # Check if this is a barcode field (^BC appears before ^FD)
            next_section = zpl_clean[fo_match.end():fo_match.end() + 100]
            bc_match = bc_pattern.search(next_section)
            
            if bc_match:
                # This is a barcode field
                fd_match = fd_pattern.search(zpl_clean, fo_match.end())
                if fd_match:
                    barcode_data = fd_match.group(1).strip()
                    barcode_height = int(bc_match.group(2))
                    
                    logger.debug(f"Rendering barcode at ({current_x}, {current_y}): {barcode_data}")
                    self._render_barcode(draw, current_x, current_y, 
                                       barcode_data, barcode_height, barcode_width)
                    position = fd_match.end()
                    continue
            
            # Look for field data (text)
            fd_match = fd_pattern.search(zpl_clean, fo_match.end())
            if fd_match and fd_match.start() < fo_match.end() + 50:
                text = fd_match.group(1).strip()
                
                if text:  # Only render non-empty text
                    logger.debug(f"Rendering text at ({current_x}, {current_y}): {text}")
                    
                    # Load font
                    font = self._get_font(current_font_size)
                    
                    # Render text
                    draw.text((current_x, current_y), text, fill='black', font=font)
                
                position = fd_match.end()
            else:
                position = fo_match.end()
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        Get font for rendering
        
        Args:
            size: Font size in points
            
        Returns:
            PIL Font object
        """
        # Try to load TrueType font
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                continue
        
        # Fallback to default font
        logger.warning("Could not load TrueType font, using default")
        return ImageFont.load_default()
    
    def _render_barcode(self, draw: ImageDraw.Draw, x: int, y: int, 
                       data: str, height: int, module_width: int = 3):
        """
        Render a simple Code 128 barcode representation
        
        Note: This is a visual representation only, not a scannable barcode.
        For production use, consider integrating a proper barcode library.
        
        Args:
            draw: PIL ImageDraw object
            x: X position
            y: Y position
            data: Barcode data
            height: Barcode height in dots
            module_width: Width of barcode modules
        """
        current_x = x
        
        # Draw start pattern (visual representation)
        draw.rectangle([current_x, y, current_x + module_width, y + height], fill='black')
        current_x += module_width * 2
        
        # Draw bars for each character (simplified pattern)
        for i, char in enumerate(data):
            # Alternate between wide and narrow bars based on character
            char_code = ord(char)
            
            # Create a simple pattern based on character code
            if char_code % 2 == 0:
                # Wide black bar
                draw.rectangle([current_x, y, current_x + module_width * 2, y + height], 
                             fill='black')
                current_x += module_width * 3
            else:
                # Narrow black bar
                draw.rectangle([current_x, y, current_x + module_width, y + height], 
                             fill='black')
                current_x += module_width * 2
        
        # Draw stop pattern
        draw.rectangle([current_x, y, current_x + module_width, y + height], fill='black')
        current_x += module_width * 2
        
        # Draw human-readable text below barcode
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20
            )
        except:
            font = ImageFont.load_default()
        
        # Center text under barcode
        text_bbox = draw.textbbox((0, 0), data, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = x + ((current_x - x) - text_width) // 2
        
        draw.text((text_x, y + height + 5), data, fill='black', font=font)
    
    def get_capabilities(self) -> dict:
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
                '^XA (Label Start)',
                '^XZ (Label End)',
                '^FO (Field Origin)',
                '^FD (Field Data)',
                '^FS (Field Separator)',
                '^CF (Change Font)',
                '^BC (Barcode Code 128)',
                '^BY (Barcode Module Width)',
                '^FX (Comments - ignored)',
            ],
            'limitations': [
                'Barcodes are visual representations only (not scannable)',
                'Limited font selection',
                'No graphics fields (^GF, ^GB)',
                'No image support (^IM)',
                'PNG output only',
            ],
            'dpi_range': {
                'min': 152,
                'max': 600,
                'default': 203
            }
        }