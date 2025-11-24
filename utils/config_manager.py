"""
Configuration Manager for Barcode Central
Handles loading and managing application configuration
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from utils.unit_converter import Unit

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration for unit settings and validation rules
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        "version": "1.0",
        "units": {
            "default_unit": "inches",
            "display_unit": "inches",
            "allow_mixed_units": True,
            "conversion_precision": 1
        },
        "validation": {
            "max_width_inches": 12,
            "max_height_inches": 12,
            "min_dimension_inches": 0.1
        }
    }
    
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize ConfigManager
        
        Args:
            config_file: Path to configuration file (default: 'config.json')
        """
        self.config_file = config_file
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from file, falling back to defaults if file doesn't exist
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading config file: {e}. Using defaults.")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            logger.info(f"Config file {self.config_file} not found. Using defaults.")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., 'units.default_unit')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., 'units.default_unit')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_default_unit(self) -> Unit:
        """
        Get default unit for label sizes
        
        Returns:
            Unit enum value
        """
        unit_str = self.get('units.default_unit', 'inches')
        unit_map = {
            'inches': Unit.INCHES,
            'in': Unit.INCHES,
            'mm': Unit.MILLIMETERS,
            'millimeters': Unit.MILLIMETERS
        }
        return unit_map.get(unit_str.lower(), Unit.INCHES)
    
    def get_display_unit(self) -> Unit:
        """
        Get display unit for UI
        
        Returns:
            Unit enum value
        """
        unit_str = self.get('units.display_unit', 'inches')
        unit_map = {
            'inches': Unit.INCHES,
            'in': Unit.INCHES,
            'mm': Unit.MILLIMETERS,
            'millimeters': Unit.MILLIMETERS
        }
        return unit_map.get(unit_str.lower(), Unit.INCHES)
    
    def get_conversion_precision(self) -> int:
        """
        Get decimal precision for unit conversions
        
        Returns:
            Number of decimal places
        """
        return self.get('units.conversion_precision', 1)
    
    def allow_mixed_units(self) -> bool:
        """
        Check if mixed units are allowed
        
        Returns:
            True if mixed units are allowed
        """
        return self.get('units.allow_mixed_units', True)
    
    def get_max_width_inches(self) -> float:
        """
        Get maximum allowed width in inches
        
        Returns:
            Maximum width in inches
        """
        return self.get('validation.max_width_inches', 12.0)
    
    def get_max_height_inches(self) -> float:
        """
        Get maximum allowed height in inches
        
        Returns:
            Maximum height in inches
        """
        return self.get('validation.max_height_inches', 12.0)
    
    def get_min_dimension_inches(self) -> float:
        """
        Get minimum allowed dimension in inches
        
        Returns:
            Minimum dimension in inches
        """
        return self.get('validation.min_dimension_inches', 0.1)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()
    
    def reset_to_defaults(self) -> None:
        """
        Reset configuration to default values
        """
        self._config = self.DEFAULT_CONFIG.copy()
        logger.info("Configuration reset to defaults")


# Global config manager instance
_config_manager = None


def get_config_manager(config_file: str = 'config.json') -> ConfigManager:
    """
    Get or create global ConfigManager instance
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager