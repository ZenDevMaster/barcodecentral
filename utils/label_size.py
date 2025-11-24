"""
Label Size Class for Barcode Central
Provides object-oriented interface for label dimensions with unit conversion
"""
from typing import Optional, Tuple, Dict, Any
from utils.unit_converter import (
    Unit, 
    parse_size_string, 
    format_size_string,
    convert_size,
    normalize_to_inches,
    inches_to_mm,
    mm_to_inches,
    inches_to_dots,
    mm_to_dots
)


class LabelSize:
    """
    Represents a label size with width and height in a specific unit
    Provides conversion methods between different units
    """
    
    def __init__(self, width: float, height: float, unit: Unit = Unit.INCHES):
        """
        Initialize LabelSize
        
        Args:
            width: Width value
            height: Height value
            unit: Unit of measurement (default: inches)
            
        Raises:
            ValueError: If dimensions are not positive
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Dimensions must be positive: width={width}, height={height}")
        
        self.width = width
        self.height = height
        self.unit = unit
    
    def to_inches(self) -> Tuple[float, float]:
        """
        Convert to inches
        
        Returns:
            Tuple of (width_inches, height_inches)
        """
        if self.unit == Unit.INCHES:
            return self.width, self.height
        elif self.unit == Unit.MILLIMETERS:
            return mm_to_inches(self.width), mm_to_inches(self.height)
        else:
            raise ValueError(f"Cannot convert {self.unit} to inches without DPI")
    
    def to_mm(self) -> Tuple[float, float]:
        """
        Convert to millimeters
        
        Returns:
            Tuple of (width_mm, height_mm)
        """
        if self.unit == Unit.MILLIMETERS:
            return self.width, self.height
        elif self.unit == Unit.INCHES:
            return inches_to_mm(self.width), inches_to_mm(self.height)
        else:
            raise ValueError(f"Cannot convert {self.unit} to millimeters without DPI")
    
    def to_dots(self, dpi: int) -> Tuple[int, int]:
        """
        Convert to dots based on DPI
        
        Args:
            dpi: Dots per inch (printer resolution)
            
        Returns:
            Tuple of (width_dots, height_dots)
        """
        if self.unit == Unit.DOTS:
            return int(self.width), int(self.height)
        elif self.unit == Unit.INCHES:
            return inches_to_dots(self.width, dpi), inches_to_dots(self.height, dpi)
        elif self.unit == Unit.MILLIMETERS:
            return mm_to_dots(self.width, dpi), mm_to_dots(self.height, dpi)
        else:
            raise ValueError(f"Unsupported unit: {self.unit}")
    
    def to_string(self, unit: Optional[Unit] = None, precision: int = 1) -> str:
        """
        Format as string in specified unit
        
        Args:
            unit: Target unit (uses current unit if not specified)
            precision: Decimal places for rounding (default: 1)
            
        Returns:
            Formatted size string (e.g., "4x6", "101.6x152.4mm")
        """
        target_unit = unit or self.unit
        
        # Convert if needed
        if target_unit != self.unit:
            width, height = convert_size(
                self.width, self.height, 
                self.unit, target_unit
            )
        else:
            width, height = self.width, self.height
        
        return format_size_string(width, height, target_unit, precision)
    
    def convert_to(self, unit: Unit, dpi: Optional[int] = None) -> 'LabelSize':
        """
        Create new LabelSize in different unit
        
        Args:
            unit: Target unit
            dpi: DPI for dots conversion (required if converting to/from dots)
            
        Returns:
            New LabelSize instance in target unit
        """
        width, height = convert_size(
            self.width, self.height,
            self.unit, unit,
            dpi
        )
        return LabelSize(width, height, unit)
    
    def to_dict(self, include_conversions: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary representation
        
        Args:
            include_conversions: Include converted values in other units
            
        Returns:
            Dictionary with size information
        """
        result = {
            'width': self.width,
            'height': self.height,
            'unit': self.unit.value,
            'formatted': self.to_string()
        }
        
        if include_conversions:
            try:
                width_in, height_in = self.to_inches()
                result['inches'] = {
                    'width': round(width_in, 2),
                    'height': round(height_in, 2),
                    'formatted': format_size_string(width_in, height_in, Unit.INCHES, 1)
                }
            except ValueError:
                pass
            
            try:
                width_mm, height_mm = self.to_mm()
                result['mm'] = {
                    'width': round(width_mm, 1),
                    'height': round(height_mm, 1),
                    'formatted': format_size_string(width_mm, height_mm, Unit.MILLIMETERS, 1)
                }
            except ValueError:
                pass
        
        return result
    
    @classmethod
    def from_string(cls, size_str: str) -> 'LabelSize':
        """
        Create LabelSize from string
        
        Args:
            size_str: Size string (e.g., "4x6", "101.6x152.4mm")
            
        Returns:
            LabelSize instance
            
        Raises:
            ValueError: If size string is invalid
        """
        width, height, unit = parse_size_string(size_str)
        return cls(width, height, unit)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LabelSize':
        """
        Create LabelSize from dictionary
        
        Args:
            data: Dictionary with 'width', 'height', and 'unit' keys
            
        Returns:
            LabelSize instance
            
        Raises:
            ValueError: If required keys are missing or invalid
        """
        if 'width' not in data or 'height' not in data:
            raise ValueError("Dictionary must contain 'width' and 'height' keys")
        
        width = float(data['width'])
        height = float(data['height'])
        
        # Parse unit
        unit_str = data.get('unit', 'inches')
        if isinstance(unit_str, Unit):
            unit = unit_str
        else:
            # Map string to Unit enum
            unit_map = {
                'inches': Unit.INCHES,
                'in': Unit.INCHES,
                'mm': Unit.MILLIMETERS,
                'millimeters': Unit.MILLIMETERS,
                'dots': Unit.DOTS
            }
            unit = unit_map.get(unit_str.lower(), Unit.INCHES)
        
        return cls(width, height, unit)
    
    def __str__(self) -> str:
        """String representation"""
        return self.to_string()
    
    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"LabelSize(width={self.width}, height={self.height}, unit={self.unit.value})"
    
    def __eq__(self, other: object) -> bool:
        """
        Check equality with another LabelSize
        Converts to inches for comparison to handle different units
        """
        if not isinstance(other, LabelSize):
            return False
        
        try:
            # Convert both to inches for comparison
            self_inches = self.to_inches()
            other_inches = other.to_inches()
            
            # Compare with small tolerance for floating point
            tolerance = 0.001
            return (
                abs(self_inches[0] - other_inches[0]) < tolerance and
                abs(self_inches[1] - other_inches[1]) < tolerance
            )
        except ValueError:
            # If conversion fails, compare raw values
            return (
                self.width == other.width and
                self.height == other.height and
                self.unit == other.unit
            )
    
    def __hash__(self) -> int:
        """Make LabelSize hashable for use in sets/dicts"""
        try:
            # Hash based on inches representation for consistency
            inches = self.to_inches()
            return hash((round(inches[0], 3), round(inches[1], 3)))
        except ValueError:
            return hash((self.width, self.height, self.unit))
    
    def is_compatible_with(self, other: 'LabelSize', tolerance: float = 0.1) -> bool:
        """
        Check if this size is compatible with another (within tolerance)
        
        Args:
            other: Another LabelSize to compare with
            tolerance: Tolerance in inches (default: 0.1)
            
        Returns:
            True if sizes are compatible within tolerance
        """
        try:
            self_inches = self.to_inches()
            other_inches = other.to_inches()
            
            width_diff = abs(self_inches[0] - other_inches[0])
            height_diff = abs(self_inches[1] - other_inches[1])
            
            return width_diff <= tolerance and height_diff <= tolerance
        except ValueError:
            return False