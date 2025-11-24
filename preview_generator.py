"""
Preview Generator Module for Barcode Central
Handles ZPL preview generation using local rendering
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
    Completely offline - no external API dependencies
    """
    
    def __init__(self, previews_dir: str = 'previews', dpi: int = 203, label_size: str = '4x6'):
        """
        Initialize PreviewGenerator with local renderer
        
        Args:
            previews_dir: Directory to store preview files (default: 'previews')
            dpi: Default DPI for previews (default: 203)
            label_size: Default label size (default: '4x6')
        """
        self.previews_dir = previews_dir
        self.default_dpi = dpi
        self.default_label_size = label_size
        
        # Initialize local renderer
        self.renderer = LocalZPLRenderer(dpi=dpi)
        
        # Ensure previews directory exists
        os.makedirs(self.previews_dir, exist_ok=True)
        
        logger.info(f"PreviewGenerator initialized with local rendering")
    
    def generate_preview(
        self,
        zpl_content: str,
        label_size: Optional[str] = None,
        dpi: Optional[int] = None,
        format: str = 'png'
    ) -> Tuple[bool, bytes, str]:
        """
        Generate preview image from ZPL content using local rendering
        
        Args:
            zpl_content: ZPL code to render
            label_size: Label size (e.g., '4x6', '4x2') - uses default if not provided
            dpi: DPI setting (152, 203, 300, 600) - uses default if not provided
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
        
        # Validate and parse label size
        try:
            width, height = self._parse_label_size(label_size)
        except ValueError as e:
            return False, b'', str(e)
        
        # Render locally
        return self.renderer.render(zpl_content, width, height, dpi)
    
    def generate_pdf(
        self,
        zpl_content: str,
        label_size: Optional[str] = None,
        dpi: Optional[int] = None
    ) -> Tuple[bool, bytes, str]:
        """
        PDF generation not supported by local renderer
        
        Args:
            zpl_content: ZPL code to render
            label_size: Label size (e.g., '4x6', '4x2')
            dpi: DPI setting (152, 203, 300, 600)
            
        Returns:
            Tuple of (success, pdf_bytes, error_message)
        """
        return False, b'', "PDF generation not supported by local renderer. Use PNG format instead."
    
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
            raise ValueError(f"Invalid label size: '{size_str}'. Error: {str(e)}")