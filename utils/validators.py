"""
Validation utilities for Barcode Central
Provides input validation and sanitization functions
"""
import re
import os
from typing import Tuple, Dict, Any, Optional
from utils.label_size import LabelSize
from utils.unit_converter import parse_size_string, Unit


def validate_template_name(name: str) -> Tuple[bool, str]:
    """
    Validate template filename
    
    Args:
        name: Template name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Template name cannot be empty"
    
    if len(name) > 100:
        return False, "Template name too long (max 100 characters)"
    
    # Allow alphanumeric, hyphens, underscores, and spaces
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
        return False, "Template name can only contain letters, numbers, hyphens, underscores, and spaces"
    
    return True, ""


def validate_printer_name(name: str) -> Tuple[bool, str]:
    """
    Validate printer name
    
    Args:
        name: Printer name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Printer name cannot be empty"
    
    if len(name) > 100:
        return False, "Printer name too long (max 100 characters)"
    
    # Allow alphanumeric, hyphens, underscores, and spaces
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
        return False, "Printer name can only contain letters, numbers, hyphens, underscores, and spaces"
    
    return True, ""


def validate_label_size(size: str) -> Tuple[bool, str]:
    """
    Validate label size format (e.g., "4x6", "4x2")
    
    Args:
        size: Label size string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not size:
        return False, "Label size cannot be empty"
    
    # Match format like "4x6" or "4.5x6.5"
    pattern = r'^\d+(\.\d+)?x\d+(\.\d+)?$'
    if not re.match(pattern, size):
        return False, "Label size must be in format 'WxH' (e.g., '4x6', '4.5x6.5')"
    
    # Parse dimensions
    try:
        width, height = size.lower().split('x')
        width_val = float(width)
        height_val = float(height)
        
        # Reasonable size limits (in inches)
        if width_val <= 0 or width_val > 12:
            return False, "Width must be between 0 and 12 inches"
        
        if height_val <= 0 or height_val > 12:
            return False, "Height must be between 0 and 12 inches"
        
    except (ValueError, AttributeError):
        return False, "Invalid label size format"
    
    return True, ""


def validate_label_size_with_unit(size: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validate label size format with unit support (e.g., "4x6", "101.6x152.4mm", "4\"x6\"")
    
    This is the new unit-aware validator that supports both metric and imperial units.
    Returns parsed data including the LabelSize object for further processing.
    
    Args:
        size: Label size string to validate
        
    Returns:
        Tuple of (is_valid, error_message, parsed_data)
        where parsed_data is a dict with 'label_size', 'width', 'height', 'unit' keys
    """
    if not size:
        return False, "Label size cannot be empty", None
    
    try:
        # Parse the size string
        label_size = LabelSize.from_string(size)
        
        # Convert to inches for validation (reasonable limits)
        width_inches, height_inches = label_size.to_inches()
        
        # Validate reasonable limits in inches (0 < dimension ≤ 12)
        if width_inches <= 0 or width_inches > 12:
            return False, f"Width must be between 0 and 12 inches (got {width_inches:.2f}\")", None
        
        if height_inches <= 0 or height_inches > 12:
            return False, f"Height must be between 0 and 12 inches (got {height_inches:.2f}\")", None
        
        # Also check minimum dimension (0.1 inches)
        if width_inches < 0.1:
            return False, f"Width too small (minimum 0.1 inches, got {width_inches:.2f}\")", None
        
        if height_inches < 0.1:
            return False, f"Height too small (minimum 0.1 inches, got {height_inches:.2f}\")", None
        
        # Build parsed data
        parsed_data = {
            'label_size': label_size,
            'width': label_size.width,
            'height': label_size.height,
            'unit': label_size.unit.value,
            'width_inches': width_inches,
            'height_inches': height_inches
        }
        
        return True, "", parsed_data
        
    except ValueError as e:
        return False, str(e), None
    except Exception as e:
        return False, f"Error validating label size: {e}", None


def validate_zpl_content(content: str) -> Tuple[bool, str]:
    """
    Basic ZPL syntax validation
    
    Args:
        content: ZPL content to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content:
        return False, "ZPL content cannot be empty"
    
    if len(content) > 100000:  # 100KB limit
        return False, "ZPL content too large (max 100KB)"
    
    # Check for basic ZPL structure
    content_upper = content.upper()
    
    # Should start with ^XA and end with ^XZ
    if not content_upper.strip().startswith('^XA'):
        return False, "ZPL content should start with ^XA"
    
    if not content_upper.strip().endswith('^XZ'):
        return False, "ZPL content should end with ^XZ"
    
    # Check for balanced ^XA and ^XZ
    xa_count = content_upper.count('^XA')
    xz_count = content_upper.count('^XZ')
    
    if xa_count != xz_count:
        return False, f"Unbalanced ^XA ({xa_count}) and ^XZ ({xz_count}) commands"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize user input for use as filename
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    if not filename:
        return "unnamed"
    
    # Remove or replace unsafe characters
    # Keep alphanumeric, hyphens, underscores, and dots
    sanitized = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Limit length
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    # Ensure not empty after sanitization
    if not sanitized:
        return "unnamed"
    
    return sanitized