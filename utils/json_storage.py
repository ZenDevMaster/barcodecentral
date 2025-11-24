"""
JSON file storage utilities for Barcode Central
Provides safe read/write operations for JSON files
"""
import json
import os
import tempfile
import shutil
from typing import Any, Dict, List
from datetime import datetime


def read_json(filepath: str, default: Any = None) -> Any:
    """
    Safely read a JSON file
    
    Args:
        filepath: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
    """
    if default is None:
        default = {}
    
    try:
        if not os.path.exists(filepath):
            return default
            
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading JSON file {filepath}: {e}")
        return default


def write_json(filepath: str, data: Any) -> bool:
    """
    Safely write data to a JSON file using atomic write
    
    Args:
        filepath: Path to the JSON file
        data: Data to write (must be JSON serializable)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Write to temporary file first (atomic write)
        with tempfile.NamedTemporaryFile('w', delete=False, 
                                        dir=os.path.dirname(filepath) or '.',
                                        encoding='utf-8') as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_filename = tmp_file.name
        
        # Move temporary file to target location
        shutil.move(tmp_filename, filepath)
        return True
        
    except (IOError, OSError, TypeError) as e:
        print(f"Error writing JSON file {filepath}: {e}")
        # Clean up temporary file if it exists
        if 'tmp_filename' in locals() and os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except OSError:
                pass
        return False


def append_to_json_array(filepath: str, item: Dict[str, Any], max_items: int = 1000) -> bool:
    """
    Append an item to a JSON array file with rotation
    
    Args:
        filepath: Path to the JSON file containing an array
        item: Item to append to the array
        max_items: Maximum number of items to keep (oldest items are removed)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read existing data
        data = read_json(filepath, default=[])
        
        # Ensure data is a list
        if not isinstance(data, list):
            print(f"Warning: {filepath} does not contain an array, creating new array")
            data = []
        
        # Add timestamp if not present
        if 'timestamp' not in item:
            item['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Append new item
        data.append(item)
        
        # Rotate if needed (keep only the most recent max_items)
        if len(data) > max_items:
            data = data[-max_items:]
        
        # Write back to file
        return write_json(filepath, data)
        
    except Exception as e:
        print(f"Error appending to JSON array {filepath}: {e}")
        return False