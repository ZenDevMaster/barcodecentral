"""
Type Converter Utility
Intelligently converts string values to appropriate types for Jinja2 templates
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def convert_variable_types(variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert string variables to appropriate types for Jinja2 templates.
    
    Conversion rules:
    - Numeric strings (e.g., '123', '45.67') -> int or float
    - Boolean-like strings ('1', '0', 'true', 'false', 'yes', 'no') -> bool
    - Other strings remain as strings
    
    Args:
        variables: Dictionary of variables (typically from form/JSON data)
        
    Returns:
        Dictionary with type-converted variables
    """
    converted = {}
    
    for key, value in variables.items():
        # Skip if not a string (already proper type)
        if not isinstance(value, str):
            converted[key] = value
            continue
        
        # Try to convert to appropriate type
        converted_value = _convert_string_value(value)
        converted[key] = converted_value
        
        # Log conversion if type changed
        if type(converted_value) != type(value):
            logger.debug(f"Converted variable '{key}': '{value}' ({type(value).__name__}) -> {converted_value} ({type(converted_value).__name__})")
    
    return converted


def _convert_string_value(value: str) -> Any:
    """
    Convert a single string value to appropriate type.
    
    Args:
        value: String value to convert
        
    Returns:
        Converted value (int, float, bool, or original string)
    """
    # Empty string stays as empty string
    if not value:
        return value
    
    # Try boolean conversion first (before numeric, since '1' and '0' are valid bools)
    bool_value = _try_convert_to_bool(value)
    if bool_value is not None:
        return bool_value
    
    # Try integer conversion
    int_value = _try_convert_to_int(value)
    if int_value is not None:
        return int_value
    
    # Try float conversion
    float_value = _try_convert_to_float(value)
    if float_value is not None:
        return float_value
    
    # Keep as string if no conversion worked
    return value


def _try_convert_to_bool(value: str) -> bool | None:
    """
    Try to convert string to boolean.
    
    Recognizes: '1', '0', 'true', 'false', 'yes', 'no', 'on', 'off' (case-insensitive)
    
    Args:
        value: String value
        
    Returns:
        Boolean value or None if not a boolean string
    """
    value_lower = value.lower().strip()
    
    # True values
    if value_lower in ('1', 'true', 'yes', 'on'):
        return True
    
    # False values
    if value_lower in ('0', 'false', 'no', 'off'):
        return False
    
    return None


def _try_convert_to_int(value: str) -> int | None:
    """
    Try to convert string to integer.
    
    Args:
        value: String value
        
    Returns:
        Integer value or None if not a valid integer
    """
    try:
        # Check if it's a pure integer (no decimal point)
        if '.' not in value:
            return int(value)
    except (ValueError, TypeError):
        pass
    
    return None


def _try_convert_to_float(value: str) -> float | None:
    """
    Try to convert string to float.
    
    Args:
        value: String value
        
    Returns:
        Float value or None if not a valid float
    """
    try:
        # Only convert if it has a decimal point
        if '.' in value:
            return float(value)
    except (ValueError, TypeError):
        pass
    
    return None