"""
Unit Conversion Module for Barcode Central
Handles conversion between inches, millimeters, and dots for label sizes
"""
import re
from enum import Enum
from typing import Tuple, Optional, Union


class Unit(Enum):
    """Supported measurement units"""
    INCHES = "inches"
    MILLIMETERS = "mm"
    DOTS = "dots"


# Conversion constants
MM_PER_INCH = 25.4
INCHES_PER_MM = 1.0 / MM_PER_INCH


def inches_to_mm(inches: float) -> float:
    """
    Convert inches to millimeters
    
    Args:
        inches: Measurement in inches
        
    Returns:
        Measurement in millimeters
    """
    return inches * MM_PER_INCH


def mm_to_inches(mm: float) -> float:
    """
    Convert millimeters to inches
    
    Args:
        mm: Measurement in millimeters
        
    Returns:
        Measurement in inches
    """
    return mm * INCHES_PER_MM


def inches_to_dots(inches: float, dpi: int) -> int:
    """
    Convert inches to dots based on DPI
    
    Args:
        inches: Measurement in inches
        dpi: Dots per inch (printer resolution)
        
    Returns:
        Measurement in dots
    """
    return int(round(inches * dpi))


def mm_to_dots(mm: float, dpi: int) -> int:
    """
    Convert millimeters to dots based on DPI
    
    Args:
        mm: Measurement in millimeters
        dpi: Dots per inch (printer resolution)
        
    Returns:
        Measurement in dots
    """
    inches = mm_to_inches(mm)
    return inches_to_dots(inches, dpi)


def dots_to_inches(dots: int, dpi: int) -> float:
    """
    Convert dots to inches based on DPI
    
    Args:
        dots: Measurement in dots
        dpi: Dots per inch (printer resolution)
        
    Returns:
        Measurement in inches
    """
    return dots / dpi


def dots_to_mm(dots: int, dpi: int) -> float:
    """
    Convert dots to millimeters based on DPI
    
    Args:
        dots: Measurement in dots
        dpi: Dots per inch (printer resolution)
        
    Returns:
        Measurement in millimeters
    """
    inches = dots_to_inches(dots, dpi)
    return inches_to_mm(inches)


def parse_size_string(size_str: str) -> Tuple[float, float, Unit]:
    """
    Parse size string into width, height, and unit
    
    Supported formats:
    - "4x6" (inches, default)
    - "4\"x6\"" (inches, explicit)
    - "101.6x152.4mm" (millimeters)
    - "4x6in" or "4x6inches" (inches, explicit)
    
    Args:
        size_str: Size string to parse
        
    Returns:
        Tuple of (width, height, unit)
        
    Raises:
        ValueError: If size string format is invalid
    """
    if not size_str:
        raise ValueError("Size string cannot be empty")
    
    size_str = size_str.strip().lower()
    
    # Remove quotes if present
    size_str = size_str.replace('"', '')
    
    # Check for unit suffix
    unit = Unit.INCHES  # Default to inches
    
    if size_str.endswith('mm'):
        unit = Unit.MILLIMETERS
        size_str = size_str[:-2].strip()
    elif size_str.endswith('inches'):
        unit = Unit.INCHES
        size_str = size_str[:-6].strip()
    elif size_str.endswith('in'):
        unit = Unit.INCHES
        size_str = size_str[:-2].strip()
    
    # Parse width x height
    if 'x' not in size_str:
        raise ValueError(f"Invalid size format: '{size_str}'. Expected format: 'WxH'")
    
    parts = size_str.split('x')
    if len(parts) != 2:
        raise ValueError(f"Invalid size format: '{size_str}'. Expected format: 'WxH'")
    
    try:
        width = float(parts[0].strip())
        height = float(parts[1].strip())
    except ValueError:
        raise ValueError(f"Invalid numeric values in size: '{size_str}'")
    
    if width <= 0 or height <= 0:
        raise ValueError(f"Dimensions must be positive: width={width}, height={height}")
    
    return width, height, unit


def format_size_string(width: float, height: float, unit: Unit, precision: int = 1) -> str:
    """
    Format size as string with unit
    
    Args:
        width: Width value
        height: Height value
        unit: Unit of measurement
        precision: Decimal places for rounding (default: 1)
        
    Returns:
        Formatted size string (e.g., "4x6", "101.6x152.4mm")
    """
    # Round to specified precision
    width = round(width, precision)
    height = round(height, precision)
    
    # Format based on unit
    if unit == Unit.MILLIMETERS:
        return f"{width}x{height}mm"
    elif unit == Unit.INCHES:
        # Remove trailing zeros and decimal point if whole number
        width_str = f"{width:.{precision}f}".rstrip('0').rstrip('.')
        height_str = f"{height:.{precision}f}".rstrip('0').rstrip('.')
        return f"{width_str}x{height_str}"
    elif unit == Unit.DOTS:
        return f"{int(width)}x{int(height)}dots"
    else:
        return f"{width}x{height}"


def convert_size(
    width: float, 
    height: float, 
    from_unit: Unit, 
    to_unit: Unit, 
    dpi: Optional[int] = None
) -> Tuple[float, float]:
    """
    Convert size from one unit to another
    
    Args:
        width: Width value
        height: Height value
        from_unit: Source unit
        to_unit: Target unit
        dpi: DPI for dots conversion (required if converting to/from dots)
        
    Returns:
        Tuple of (converted_width, converted_height)
        
    Raises:
        ValueError: If DPI is required but not provided
    """
    # No conversion needed
    if from_unit == to_unit:
        return width, height
    
    # Convert to inches first (canonical format)
    if from_unit == Unit.INCHES:
        width_inches = width
        height_inches = height
    elif from_unit == Unit.MILLIMETERS:
        width_inches = mm_to_inches(width)
        height_inches = mm_to_inches(height)
    elif from_unit == Unit.DOTS:
        if dpi is None:
            raise ValueError("DPI is required for dots conversion")
        width_inches = dots_to_inches(int(width), dpi)
        height_inches = dots_to_inches(int(height), dpi)
    else:
        raise ValueError(f"Unsupported source unit: {from_unit}")
    
    # Convert from inches to target unit
    if to_unit == Unit.INCHES:
        return width_inches, height_inches
    elif to_unit == Unit.MILLIMETERS:
        return inches_to_mm(width_inches), inches_to_mm(height_inches)
    elif to_unit == Unit.DOTS:
        if dpi is None:
            raise ValueError("DPI is required for dots conversion")
        return inches_to_dots(width_inches, dpi), inches_to_dots(height_inches, dpi)
    else:
        raise ValueError(f"Unsupported target unit: {to_unit}")


def normalize_to_inches(width: float, height: float, unit: Unit) -> Tuple[float, float]:
    """
    Convert any unit to inches (canonical format)
    
    Args:
        width: Width value
        height: Height value
        unit: Source unit
        
    Returns:
        Tuple of (width_inches, height_inches)
    """
    if unit == Unit.INCHES:
        return width, height
    elif unit == Unit.MILLIMETERS:
        return mm_to_inches(width), mm_to_inches(height)
    else:
        raise ValueError(f"Cannot normalize {unit} to inches without DPI")


def parse_and_normalize(size_str: str) -> Tuple[float, float]:
    """
    Parse size string and normalize to inches
    
    Args:
        size_str: Size string to parse
        
    Returns:
        Tuple of (width_inches, height_inches)
        
    Raises:
        ValueError: If size string is invalid
    """
    width, height, unit = parse_size_string(size_str)
    return normalize_to_inches(width, height, unit)