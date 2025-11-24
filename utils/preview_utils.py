"""
Preview Utilities for Barcode Central
Helper functions for preview generation and management
"""
import uuid
import re
from typing import Tuple, Optional


def parse_label_size(size_str: str) -> Tuple[float, float]:
    """
    Parse label size string into width and height
    
    Args:
        size_str: Label size string (e.g., '4x6', '4.5x2.5')
        
    Returns:
        Tuple of (width, height) in inches
        
    Raises:
        ValueError: If size string is invalid
    """
    if not size_str or 'x' not in size_str.lower():
        raise ValueError(f"Invalid label size format: '{size_str}'. Expected format: 'WxH' (e.g., '4x6')")
    
    try:
        parts = size_str.lower().split('x')
        if len(parts) != 2:
            raise ValueError(f"Invalid label size format: '{size_str}'. Expected format: 'WxH'")
        
        width = float(parts[0].strip())
        height = float(parts[1].strip())
        
        # Validate dimensions
        if width <= 0 or height <= 0:
            raise ValueError(f"Label dimensions must be positive: {size_str}")
        
        if width > 12 or height > 12:
            raise ValueError(f"Label dimensions too large (max 12 inches): {size_str}")
        
        return width, height
        
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid label size: '{size_str}'. Error: {str(e)}")


def validate_label_size(size_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate label size format
    
    Args:
        size_str: Label size string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parse_label_size(size_str)
        return True, None
    except ValueError as e:
        return False, str(e)


def calculate_preview_dimensions(label_size: str, dpi: int) -> Tuple[int, int]:
    """
    Calculate preview image dimensions in pixels
    
    Args:
        label_size: Label size string (e.g., '4x6')
        dpi: DPI setting
        
    Returns:
        Tuple of (width_pixels, height_pixels)
        
    Raises:
        ValueError: If label size is invalid
    """
    width_inches, height_inches = parse_label_size(label_size)
    
    # Calculate pixel dimensions
    width_pixels = int(width_inches * dpi)
    height_pixels = int(height_inches * dpi)
    
    return width_pixels, height_pixels


def generate_preview_filename(prefix: str = 'preview', extension: str = 'png') -> str:
    """
    Generate unique preview filename using UUID
    
    Args:
        prefix: Filename prefix (default: 'preview')
        extension: File extension without dot (default: 'png')
        
    Returns:
        Unique filename string
    """
    unique_id = uuid.uuid4()
    
    # Sanitize prefix (remove special characters)
    safe_prefix = re.sub(r'[^a-zA-Z0-9_-]', '', prefix)
    
    # Ensure extension doesn't have leading dot
    extension = extension.lstrip('.')
    
    if safe_prefix:
        return f"{safe_prefix}_{unique_id}.{extension}"
    else:
        return f"{unique_id}.{extension}"


def get_labelary_url(dpi: int, width: float, height: float, format: str = 'png') -> str:
    """
    Construct Labelary API URL
    
    Args:
        dpi: Labelary DPI value (6, 8, 12, or 24)
        width: Label width in inches
        height: Label height in inches
        format: Output format ('png' or 'pdf')
        
    Returns:
        Labelary API URL string
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate DPI
    valid_dpis = [6, 8, 12, 24]
    if dpi not in valid_dpis:
        raise ValueError(f"Invalid Labelary DPI: {dpi}. Must be one of {valid_dpis}")
    
    # Validate format
    if format not in ['png', 'pdf']:
        raise ValueError(f"Invalid format: {format}. Must be 'png' or 'pdf'")
    
    # Validate dimensions
    if width <= 0 or height <= 0:
        raise ValueError("Label dimensions must be positive")
    
    if width > 12 or height > 12:
        raise ValueError("Label dimensions too large (max 12 inches)")
    
    # Construct URL
    base_url = "http://api.labelary.com/v1/printers"
    url = f"{base_url}/{dpi}dpi/labels/{width}x{height}/0/"
    
    return url


def map_printer_dpi_to_labelary(printer_dpi: int) -> Optional[int]:
    """
    Map printer DPI to Labelary API DPI value
    
    Labelary uses different DPI values:
    - 6dpi = 152 DPI printers
    - 8dpi = 203 DPI printers
    - 12dpi = 300 DPI printers
    - 24dpi = 600 DPI printers
    
    Args:
        printer_dpi: Actual printer DPI (152, 203, 300, 600)
        
    Returns:
        Labelary DPI value or None if not supported
    """
    dpi_mapping = {
        152: 6,
        203: 8,
        300: 12,
        600: 24
    }
    
    return dpi_mapping.get(printer_dpi)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted size string (e.g., '1.5 MB', '256 KB')
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def sanitize_preview_filename(filename: str) -> str:
    """
    Sanitize filename for preview storage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    name_part, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name_part) > 50:
        name_part = name_part[:50]
    
    return f"{name_part}.{ext}" if ext else name_part


def extract_label_size_from_template(template_content: str) -> Optional[str]:
    """
    Extract label size from template metadata
    
    Args:
        template_content: Template content with metadata
        
    Returns:
        Label size string or None if not found
    """
    # Look for ^FX size: metadata
    pattern = r'\^FX\s+size:\s*([0-9.]+x[0-9.]+)'
    match = re.search(pattern, template_content, re.IGNORECASE)
    
    if match:
        return match.group(1)
    
    return None