"""
Preview Generator Module for Barcode Central
Handles ZPL preview generation using Labelary API
"""
import os
import logging
import uuid
import requests
import struct
from typing import Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
# from local_zpl_renderer import LocalZPLRenderer  # Preserved but not used - using Labelary API instead
from utils.label_size import LabelSize

logger = logging.getLogger(__name__)


class PreviewGenerator:
    """
    Generates label previews using Labelary API
    Supports both PNG and PDF output formats
    """
    
    def __init__(self, previews_dir: str = 'previews', dpi: int = 203, label_size: str = '4x6'):
        """
        Initialize PreviewGenerator with Labelary API
        
        Args:
            previews_dir: Directory to store preview files (default: 'previews')
            dpi: Default DPI for previews (default: 203)
            label_size: Default label size (default: '4x6')
        """
        self.previews_dir = previews_dir
        self.default_dpi = dpi
        self.default_label_size = label_size
        
        # Labelary API configuration
        self.LABELARY_BASE_URL = "http://api.labelary.com/v1/printers"
        self.LABELARY_TIMEOUT = 10  # seconds
        
        # Local renderer preserved but not used
        # self.renderer = LocalZPLRenderer(dpi=dpi)  # Using Labelary API instead
        
        # Ensure previews directory exists
        os.makedirs(self.previews_dir, exist_ok=True)
        
        logger.info(f"PreviewGenerator initialized with Labelary API")
    
    def generate_preview(
        self,
        zpl_content: str,
        label_size: Optional[str] = None,
        dpi: Optional[int] = None,
        format: str = 'png'
    ) -> Tuple[bool, bytes, str]:
        """
        Generate preview image from ZPL content using Labelary API
        
        Args:
            zpl_content: ZPL code to render
            label_size: Label size (e.g., '4x6', '4x2') - uses default if not provided
            dpi: DPI setting (152, 203, 300, 600) - uses default if not provided
            format: Output format ('png' or 'pdf')
            
        Returns:
            Tuple of (success, image_bytes, error_message)
        """
        # Use defaults if not provided
        label_size = label_size or self.default_label_size
        dpi = dpi or self.default_dpi
        
        # Validate format
        if format not in ['png', 'pdf']:
            return False, b'', f"Invalid format '{format}'. Must be 'png' or 'pdf'"
        
        # Validate and parse label size
        try:
            width, height = self._parse_label_size(label_size)
        except ValueError as e:
            return False, b'', str(e)
        
        # Map printer DPI to Labelary dpmm (dots per millimeter)
        from utils.preview_utils import map_printer_dpi_to_labelary
        labelary_dpmm = map_printer_dpi_to_labelary(dpi)
        if not labelary_dpmm:
            return False, b'', f"Unsupported DPI: {dpi}. Must be 152, 203, 300, or 600"
        
        # Build Labelary URL - note: Labelary uses 'dpmm' in URL but values are dpmm
        url = f"{self.LABELARY_BASE_URL}/{labelary_dpmm}dpmm/labels/{width}x{height}/0/"
        
        # Set headers based on format
        headers = {
            'Accept': 'application/pdf' if format == 'pdf' else 'image/png'
        }
        
        try:
            # Send request to Labelary API
            logger.debug(f"Sending request to Labelary: {url}")
            response = requests.post(
                url,
                data=zpl_content.encode('utf-8'),
                headers=headers,
                timeout=self.LABELARY_TIMEOUT
            )
            
            if response.status_code == 200:
                image_bytes = response.content
                
                # Add DPI metadata to PNG files by inserting pHYs chunk (PDF doesn't need this)
                if format == 'png':
                    try:
                        image_bytes = self._add_png_dpi_metadata(image_bytes, dpi)
                        logger.debug(f"Added DPI metadata ({dpi}) to PNG image")
                    except Exception as e:
                        # If adding DPI fails, use original image
                        logger.warning(f"Failed to add DPI metadata: {e}, using original image")
                        image_bytes = response.content
                
                logger.info(f"Successfully generated {format.upper()} preview via Labelary ({len(image_bytes)} bytes)")
                return True, image_bytes, ""
            else:
                error_msg = f"Labelary API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, b'', error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "Labelary API timeout - service may be unavailable"
            logger.error(error_msg)
            return False, b'', error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Labelary API - check internet connection"
            logger.error(error_msg)
            return False, b'', error_msg
        except Exception as e:
            error_msg = f"Labelary API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, b'', error_msg
    
    def generate_pdf(
        self,
        zpl_content: str,
        label_size: Optional[str] = None,
        dpi: Optional[int] = None
    ) -> Tuple[bool, bytes, str]:
        """
        Generate PDF preview using Labelary API
        
        Args:
            zpl_content: ZPL code to render
            label_size: Label size (e.g., '4x6', '4x2')
            dpi: DPI setting (152, 203, 300, 600)
            
        Returns:
            Tuple of (success, pdf_bytes, error_message)
        """
        return self.generate_preview(zpl_content, label_size, dpi, format='pdf')
    
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
        
        Args:
            zpl_content: ZPL code to render
            filename: Filename to save as (generates UUID if not provided)
            label_size: Label size (e.g., '4x6', '4x2')
            dpi: DPI setting (152, 203, 300, 600)
            format: Output format ('png' or 'pdf')
            
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
            
            logger.info(f"Saved preview to: {filepath}")
            return True, filename, ""
            
        except Exception as e:
            error_msg = f"Error saving preview: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def get_preview_path(self, filename: str) -> str:
        """
        Get full path to preview file
        
        Args:
            filename: Preview filename
            
        Returns:
            Full path to preview file
        """
        return os.path.join(self.previews_dir, filename)
    
    def preview_exists(self, filename: str) -> bool:
        """
        Check if preview file exists
        
        Args:
            filename: Preview filename
            
        Returns:
            True if file exists, False otherwise
        """
        filepath = self.get_preview_path(filename)
        return os.path.exists(filepath)
    
    def cleanup_old_previews(self, days: int = 7) -> Tuple[int, int]:
        """
        Delete preview files older than specified days
        
        Args:
            days: Number of days to keep previews (default: 7)
            
        Returns:
            Tuple of (files_deleted, errors)
        """
        if days < 1:
            logger.warning("Invalid days parameter for cleanup, must be >= 1")
            return 0, 0
        
        cutoff_time = datetime.now() - timedelta(days=days)
        files_deleted = 0
        errors = 0
        
        try:
            for filename in os.listdir(self.previews_dir):
                filepath = os.path.join(self.previews_dir, filename)
                
                # Skip directories
                if not os.path.isfile(filepath):
                    continue
                
                # Check file age
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_time:
                    try:
                        os.remove(filepath)
                        files_deleted += 1
                        logger.debug(f"Deleted old preview: {filename}")
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error deleting {filename}: {e}")
            
            logger.info(f"Cleanup completed: {files_deleted} files deleted, {errors} errors")
            return files_deleted, errors
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return files_deleted, errors
    
    def _parse_label_size(self, size_str: str) -> Tuple[float, float]:
        """
        Parse label size string into width and height in inches
        
        Supports both legacy format ("4x6") and new unit-aware formats
        ("101.6x152.4mm", "4\"x6\""). Always returns dimensions in inches.
        
        Args:
            size_str: Label size string (e.g., '4x6', '101.6x152.4mm', '4\"x6\"')
            
        Returns:
            Tuple of (width, height) in inches
            
        Raises:
            ValueError: If size string is invalid
        """
        if not size_str:
            raise ValueError("Label size cannot be empty")
        
        try:
            # Use the new unit-aware parser
            label_size = LabelSize.from_string(size_str)
            
            # Convert to inches (Labelary API requirement)
            width_inches, height_inches = label_size.to_inches()
            
            # Validate dimensions
            if width_inches <= 0 or height_inches <= 0:
                raise ValueError(f"Label dimensions must be positive: {size_str}")
            
            if width_inches > 12 or height_inches > 12:
                raise ValueError(f"Label dimensions too large (max 12 inches): {size_str}")
            
            return width_inches, height_inches
            
        except ValueError as e:
            # If new parser fails, try legacy format for backward compatibility
            if 'x' in size_str.lower():
                try:
                    parts = size_str.lower().replace('"', '').split('x')
                    if len(parts) == 2:
                        width = float(parts[0].strip())
                        height = float(parts[1].strip())
                        
                        if width > 0 and height > 0 and width <= 12 and height <= 12:
                            return width, height
                except (ValueError, AttributeError):
                    pass
            
            # Re-raise the original error
    
    def _add_png_dpi_metadata(self, png_bytes: bytes, dpi: int) -> bytes:
        """
        Add pHYs chunk to PNG to set DPI metadata without re-encoding the image
        
        Args:
            png_bytes: Original PNG image bytes
            dpi: DPI value to set
            
        Returns:
            PNG bytes with pHYs chunk added
        """
        # Convert DPI to pixels per meter (PNG uses meters, not inches)
        # 1 inch = 0.0254 meters, so pixels_per_meter = dpi / 0.0254
        pixels_per_meter = int(dpi / 0.0254)
        
        # PNG signature
        png_signature = b'\x89PNG\r\n\x1a\n'
        
        # Check if this is a valid PNG
        if not png_bytes.startswith(png_signature):
            raise ValueError("Not a valid PNG file")
        
        # Find the IDAT chunk (where we'll insert pHYs before it)
        idat_pos = png_bytes.find(b'IDAT')
        if idat_pos == -1:
            raise ValueError("Could not find IDAT chunk in PNG")
        
        # pHYs chunk format:
        # - 4 bytes: chunk length (9 bytes for pHYs data)
        # - 4 bytes: chunk type ('pHYs')
        # - 4 bytes: pixels per unit, X axis
        # - 4 bytes: pixels per unit, Y axis  
        # - 1 byte: unit specifier (1 = meter)
        # - 4 bytes: CRC
        
        phys_data = struct.pack('>II', pixels_per_meter, pixels_per_meter) + b'\x01'
        
        # Calculate CRC for pHYs chunk (CRC of type + data)
        import zlib
        phys_chunk_data = b'pHYs' + phys_data
        crc = zlib.crc32(phys_chunk_data) & 0xffffffff
        
        # Build complete pHYs chunk
        phys_chunk = struct.pack('>I', 9) + phys_chunk_data + struct.pack('>I', crc)
        
        # Insert pHYs chunk before IDAT (at position idat_pos - 4 for the length field)
        insert_pos = idat_pos - 4
        result = png_bytes[:insert_pos] + phys_chunk + png_bytes[insert_pos:]
        
        return result