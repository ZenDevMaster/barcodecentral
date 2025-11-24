"""
Printer Manager Module for Barcode Central
Handles printer configuration, validation, and ZPL communication via TCP sockets
"""
import socket
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from utils.json_storage import read_json, write_json
from utils.validators import validate_label_size, validate_label_size_with_unit
from utils.label_size import LabelSize
from utils.unit_converter import Unit

# Configure logging
logger = logging.getLogger(__name__)


class PrinterManager:
    """Manages printer configurations and ZPL communication"""
    
    def __init__(self, printers_file: str = 'printers.json'):
        """
        Initialize PrinterManager
        
        Args:
            printers_file: Path to printers configuration JSON file
        """
        self.printers_file = printers_file
        self._printers_cache = None
        self._cache_timestamp = None
    
    def _load_printers(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load printers from configuration file with caching
        
        Args:
            force_reload: Force reload from file, bypassing cache
            
        Returns:
            Dictionary containing printers configuration
        """
        # Simple cache to avoid repeated file reads
        if not force_reload and self._printers_cache is not None:
            return self._printers_cache
        
        data = read_json(self.printers_file, default={'printers': []})
        self._printers_cache = data
        self._cache_timestamp = datetime.utcnow()
        return data
    
    def _save_printers(self, data: Dict[str, Any]) -> bool:
        """
        Save printers configuration to file
        
        Args:
            data: Printers configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        success = write_json(self.printers_file, data)
        if success:
            # Invalidate cache
            self._printers_cache = None
            logger.info(f"Printers configuration saved to {self.printers_file}")
        return success
    
    def list_printers(self) -> List[Dict[str, Any]]:
        """
        Get list of all configured printers
        
        Returns:
            List of printer dictionaries
        """
        data = self._load_printers()
        return data.get('printers', [])
    
    def get_printer(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific printer by ID
        
        Args:
            printer_id: Unique printer identifier
            
        Returns:
            Printer dictionary or None if not found
        """
        printers = self.list_printers()
        for printer in printers:
            if printer.get('id') == printer_id:
                return printer
        return None
    
    def add_printer(self, printer_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add new printer to configuration
        
        Supports both legacy format (list of size strings) and new format (list of size dicts).
        
        Args:
            printer_data: Dictionary containing printer configuration
            
        Returns:
            Tuple of (success, message)
        """
        # Validate required fields
        required_fields = ['id', 'name', 'ip', 'port', 'supported_sizes', 'dpi']
        for field in required_fields:
            if field not in printer_data:
                return False, f"Missing required field: {field}"
        
        # Validate printer ID format (filesystem-safe)
        printer_id = printer_data['id']
        if not printer_id or not isinstance(printer_id, str):
            return False, "Printer ID must be a non-empty string"
        
        if not printer_id.replace('-', '').replace('_', '').isalnum():
            return False, "Printer ID can only contain letters, numbers, hyphens, and underscores"
        
        # Check if printer ID already exists
        if self.get_printer(printer_id):
            return False, f"Printer with ID '{printer_id}' already exists"
        
        # Validate IP address format
        ip = printer_data['ip']
        if not self._validate_ip(ip):
            return False, f"Invalid IP address: {ip}"
        
        # Validate port
        port = printer_data['port']
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False, f"Port must be between 1 and 65535"
        
        # Validate and normalize supported sizes
        supported_sizes = printer_data['supported_sizes']
        if not isinstance(supported_sizes, list) or len(supported_sizes) == 0:
            return False, "supported_sizes must be a non-empty list"
        
        # Process sizes - support both string format and dict format
        supported_sizes_v2 = []  # New format with unit info
        supported_sizes_legacy = []  # Legacy format (strings in inches)
        
        for size in supported_sizes:
            if isinstance(size, str):
                # Legacy string format - validate and convert
                is_valid, error, parsed_data = validate_label_size_with_unit(size)
                if not is_valid:
                    # Try legacy validator
                    is_valid_legacy, error_legacy = validate_label_size(size)
                    if not is_valid_legacy:
                        return False, f"Invalid label size '{size}': {error}"
                    # Use legacy format
                    supported_sizes_legacy.append(size)
                else:
                    # Convert to new format
                    label_size = parsed_data['label_size']
                    supported_sizes_v2.append({
                        'width': label_size.width,
                        'height': label_size.height,
                        'unit': label_size.unit.value
                    })
                    # Also store legacy format (in inches)
                    width_in, height_in = label_size.to_inches()
                    legacy_str = f"{width_in:.1f}x{height_in:.1f}".replace('.0', '')
                    supported_sizes_legacy.append(legacy_str)
            elif isinstance(size, dict):
                # New dict format
                try:
                    label_size = LabelSize.from_dict(size)
                    supported_sizes_v2.append({
                        'width': label_size.width,
                        'height': label_size.height,
                        'unit': label_size.unit.value
                    })
                    # Also store legacy format
                    width_in, height_in = label_size.to_inches()
                    legacy_str = f"{width_in:.1f}x{height_in:.1f}".replace('.0', '')
                    supported_sizes_legacy.append(legacy_str)
                except ValueError as e:
                    return False, f"Invalid label size dict: {e}"
            else:
                return False, f"Invalid size format: {size}"
        
        # Validate DPI
        dpi = printer_data['dpi']
        if not isinstance(dpi, int) or dpi <= 0:
            return False, "DPI must be a positive integer"
        
        # Set default enabled status if not provided
        if 'enabled' not in printer_data:
            printer_data['enabled'] = True
        
        # Set default unit if not provided
        if 'default_unit' not in printer_data:
            printer_data['default_unit'] = 'inches'
        
        # Store both formats for backward compatibility
        printer_data['supported_sizes'] = supported_sizes_legacy  # Legacy format
        printer_data['supported_sizes_v2'] = supported_sizes_v2  # New format
        
        # Add printer to configuration
        data = self._load_printers()
        data['printers'].append(printer_data)
        
        if self._save_printers(data):
            logger.info(f"Added printer: {printer_id} ({printer_data['name']})")
            return True, "Printer added successfully"
        else:
            return False, "Failed to save printer configuration"
    
    def update_printer(self, printer_id: str, printer_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update existing printer configuration
        
        Supports both legacy format (list of size strings) and new format (list of size dicts).
        
        Args:
            printer_id: Printer ID to update
            printer_data: Updated printer configuration
            
        Returns:
            Tuple of (success, message)
        """
        # Force reload to ensure we have fresh data from disk
        data = self._load_printers(force_reload=True)
        printers = data.get('printers', [])
        
        # Find printer index
        printer_index = None
        for i, printer in enumerate(printers):
            if printer.get('id') == printer_id:
                printer_index = i
                break
        
        if printer_index is None:
            return False, f"Printer '{printer_id}' not found"
        
        # Validate updated fields if provided
        if 'ip' in printer_data:
            if not self._validate_ip(printer_data['ip']):
                return False, f"Invalid IP address: {printer_data['ip']}"
        
        if 'port' in printer_data:
            port = printer_data['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False, f"Port must be between 1 and 65535"
        
        if 'supported_sizes' in printer_data:
            supported_sizes = printer_data['supported_sizes']
            if not isinstance(supported_sizes, list) or len(supported_sizes) == 0:
                return False, "supported_sizes must be a non-empty list"
            
            # Process sizes - support both string format and dict format
            supported_sizes_v2 = []
            supported_sizes_legacy = []
            
            for size in supported_sizes:
                if isinstance(size, str):
                    is_valid, error, parsed_data = validate_label_size_with_unit(size)
                    if not is_valid:
                        is_valid_legacy, error_legacy = validate_label_size(size)
                        if not is_valid_legacy:
                            return False, f"Invalid label size '{size}': {error}"
                        supported_sizes_legacy.append(size)
                    else:
                        label_size = parsed_data['label_size']
                        supported_sizes_v2.append({
                            'width': label_size.width,
                            'height': label_size.height,
                            'unit': label_size.unit.value
                        })
                        width_in, height_in = label_size.to_inches()
                        legacy_str = f"{width_in:.1f}x{height_in:.1f}".replace('.0', '')
                        supported_sizes_legacy.append(legacy_str)
                elif isinstance(size, dict):
                    try:
                        label_size = LabelSize.from_dict(size)
                        supported_sizes_v2.append({
                            'width': label_size.width,
                            'height': label_size.height,
                            'unit': label_size.unit.value
                        })
                        width_in, height_in = label_size.to_inches()
                        legacy_str = f"{width_in:.1f}x{height_in:.1f}".replace('.0', '')
                        supported_sizes_legacy.append(legacy_str)
                    except ValueError as e:
                        return False, f"Invalid label size dict: {e}"
            
            # Update both formats
            printer_data['supported_sizes'] = supported_sizes_legacy
            printer_data['supported_sizes_v2'] = supported_sizes_v2
        
        if 'dpi' in printer_data:
            dpi = printer_data['dpi']
            if not isinstance(dpi, int) or dpi <= 0:
                return False, "DPI must be a positive integer"
        
        # Update printer (merge with existing data)
        printers[printer_index].update(printer_data)
        
        # Ensure ID doesn't change
        printers[printer_index]['id'] = printer_id
        
        if self._save_printers(data):
            logger.info(f"Updated printer: {printer_id}")
            return True, "Printer updated successfully"
        else:
            return False, "Failed to save printer configuration"
    
    def delete_printer(self, printer_id: str) -> Tuple[bool, str]:
        """
        Delete printer from configuration
        
        Args:
            printer_id: Printer ID to delete
            
        Returns:
            Tuple of (success, message)
        """
        data = self._load_printers()
        printers = data.get('printers', [])
        
        # Find and remove printer
        original_count = len(printers)
        printers = [p for p in printers if p.get('id') != printer_id]
        
        if len(printers) == original_count:
            return False, f"Printer '{printer_id}' not found"
        
        data['printers'] = printers
        
        if self._save_printers(data):
            logger.info(f"Deleted printer: {printer_id}")
            return True, "Printer deleted successfully"
        else:
            return False, "Failed to save printer configuration"
    
    def validate_printer_compatibility(self, printer_id: str, label_size: str) -> Tuple[bool, str]:
        """
        Check if printer supports the specified label size
        
        Supports unit-aware comparison - converts sizes to inches for comparison.
        
        Args:
            printer_id: Printer ID to check
            label_size: Label size to validate (e.g., "4x6", "101.6x152.4mm")
            
        Returns:
            Tuple of (is_compatible, message)
        """
        printer = self.get_printer(printer_id)
        if not printer:
            return False, f"Printer '{printer_id}' not found"
        
        if not printer.get('enabled', True):
            return False, f"Printer '{printer_id}' is disabled"
        
        # Try to parse the requested size
        try:
            requested_size = LabelSize.from_string(label_size)
        except ValueError as e:
            return False, f"Invalid label size format: {e}"
        
        # Check against supported sizes (try v2 format first, fall back to legacy)
        supported_sizes_v2 = printer.get('supported_sizes_v2', [])
        supported_sizes_legacy = printer.get('supported_sizes', [])
        
        # Check v2 format (unit-aware)
        if supported_sizes_v2:
            for size_dict in supported_sizes_v2:
                try:
                    supported_size = LabelSize.from_dict(size_dict)
                    if requested_size.is_compatible_with(supported_size, tolerance=0.1):
                        return True, "Printer is compatible"
                except (ValueError, Exception):
                    continue
        
        # Fall back to legacy format (string comparison in inches)
        if supported_sizes_legacy:
            # Convert requested size to inches for comparison
            try:
                req_width, req_height = requested_size.to_inches()
                req_str = f"{req_width:.1f}x{req_height:.1f}".replace('.0', '')
                
                if req_str in supported_sizes_legacy:
                    return True, "Printer is compatible"
                
                # Also try exact string match
                if label_size in supported_sizes_legacy:
                    return True, "Printer is compatible"
            except (ValueError, Exception):
                pass
        
        # Not compatible
        supported_list = supported_sizes_legacy if supported_sizes_legacy else [
            f"{s['width']}x{s['height']}{s['unit']}" for s in supported_sizes_v2
        ]
        return False, f"Printer does not support label size '{label_size}'. Supported sizes: {', '.join(supported_list)}"
    
    def test_printer_connection(self, printer_id: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        Test TCP connection to printer
        
        Args:
            printer_id: Printer ID to test
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple of (success, message)
        """
        printer = self.get_printer(printer_id)
        if not printer:
            return False, f"Printer '{printer_id}' not found"
        
        ip = printer.get('ip')
        port = printer.get('port', 9100)
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((ip, port))
                logger.info(f"Successfully connected to printer {printer_id} at {ip}:{port}")
                return True, f"Connection successful to {ip}:{port}"
        except socket.timeout:
            error_msg = f"Connection to {ip}:{port} timed out after {timeout} seconds"
            logger.warning(f"Printer {printer_id}: {error_msg}")
            return False, error_msg
        except socket.error as e:
            error_msg = f"Failed to connect to {ip}:{port}: {str(e)}"
            logger.error(f"Printer {printer_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error testing connection: {str(e)}"
            logger.error(f"Printer {printer_id}: {error_msg}")
            return False, error_msg
    
    def send_zpl(self, printer_id: str, zpl_content: str, quantity: int = 1, timeout: int = 5) -> Tuple[bool, str]:
        """
        Send ZPL content to printer via TCP socket
        
        Args:
            printer_id: Printer ID to send to
            zpl_content: ZPL code to send
            quantity: Number of copies to print (1-100)
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple of (success, message)
        """
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            return False, "Quantity must be between 1 and 100"
        
        # Get printer configuration
        printer = self.get_printer(printer_id)
        if not printer:
            return False, f"Printer '{printer_id}' not found"
        
        if not printer.get('enabled', True):
            return False, f"Printer '{printer_id}' is disabled"
        
        # Validate ZPL content
        if not zpl_content or not isinstance(zpl_content, str):
            return False, "ZPL content cannot be empty"
        
        if len(zpl_content) > 100000:  # 100KB limit
            return False, "ZPL content too large (max 100KB)"
        
        ip = printer.get('ip')
        port = printer.get('port', 9100)
        
        # Log ZPL content BEFORE attempting to send
        zpl_length = len(zpl_content)
        zpl_preview = zpl_content[:200] + '...' if zpl_length > 200 else zpl_content
        logger.info(f"[SEND_ZPL] Printer: {printer_id} ({ip}:{port})")
        logger.info(f"[SEND_ZPL] ZPL Length: {zpl_length} bytes")
        logger.info(f"[SEND_ZPL] ZPL Preview (first 200 chars): {repr(zpl_preview)}")
        logger.info(f"[SEND_ZPL] Quantity: {quantity} copies")
        logger.info(f"[SEND_ZPL] Timeout: {timeout} seconds")
        
        try:
            # Send ZPL for each copy
            for copy_num in range(quantity):
                logger.info(f"[SEND_ZPL] Starting copy {copy_num + 1}/{quantity}")
                
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                logger.info(f"[SEND_ZPL] Socket created: {sock}")
                
                try:
                    # Set timeout
                    sock.settimeout(timeout)
                    logger.info(f"[SEND_ZPL] Socket timeout set to {timeout}s")
                    
                    # Connect
                    logger.info(f"[SEND_ZPL] Attempting connection to {ip}:{port}...")
                    sock.connect((ip, port))
                    logger.info(f"[SEND_ZPL] Successfully connected to {ip}:{port}")
                    
                    # Check socket state before sending
                    try:
                        peer_name = sock.getpeername()
                        logger.info(f"[SEND_ZPL] Socket peer: {peer_name}")
                    except Exception as e:
                        logger.warning(f"[SEND_ZPL] Could not get peer name: {e}")
                    
                    # Encode ZPL
                    zpl_bytes = zpl_content.encode('utf-8')
                    logger.info(f"[SEND_ZPL] Encoded ZPL to {len(zpl_bytes)} bytes")
                    
                    # Send data
                    logger.info(f"[SEND_ZPL] Calling sendall() with {len(zpl_bytes)} bytes...")
                    sock.sendall(zpl_bytes)
                    logger.info(f"[SEND_ZPL] sendall() completed successfully")
                    
                    # Verify socket is still connected
                    try:
                        peer_name = sock.getpeername()
                        logger.info(f"[SEND_ZPL] Socket still connected to {peer_name} after send")
                    except Exception as e:
                        logger.warning(f"[SEND_ZPL] Socket disconnected after send: {e}")
                    
                    # CRITICAL: Wait for data to be transmitted before closing
                    logger.info(f"[SEND_ZPL] Waiting 0.5s for data transmission...")
                    time.sleep(0.5)
                    logger.info(f"[SEND_ZPL] Wait complete")
                    
                    # Properly shutdown the socket before closing
                    logger.info(f"[SEND_ZPL] Attempting socket shutdown...")
                    try:
                        sock.shutdown(socket.SHUT_WR)
                        logger.info(f"[SEND_ZPL] Socket shutdown successful")
                    except Exception as e:
                        logger.warning(f"[SEND_ZPL] Socket shutdown failed (may be normal): {e}")
                    
                    logger.info(f"[SEND_ZPL] Closing socket...")
                    sock.close()
                    logger.info(f"[SEND_ZPL] Socket closed")
                    
                    logger.info(f"[SEND_ZPL] ✓ Successfully sent copy {copy_num + 1}/{quantity} to {printer_id}")
                    
                except Exception as e:
                    logger.error(f"[SEND_ZPL] ✗ Error during copy {copy_num + 1}/{quantity}: {type(e).__name__}: {e}")
                    sock.close()
                    raise
            
            logger.info(f"[SEND_ZPL] ✓✓✓ ALL COPIES SENT SUCCESSFULLY ✓✓✓")
            return True, f"Successfully sent {quantity} label(s) to printer"
            
        except socket.timeout:
            error_msg = f"Connection to {ip}:{port} timed out after {timeout} seconds"
            logger.error(f"Printer {printer_id}: {error_msg}")
            return False, error_msg
        except socket.error as e:
            error_msg = f"Failed to connect to {ip}:{port}: {str(e)}"
            logger.error(f"Printer {printer_id}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error sending ZPL: {str(e)}"
            logger.error(f"Printer {printer_id}: {error_msg}")
            return False, error_msg
    
    def _validate_ip(self, ip: str) -> bool:
        """
        Validate IPv4 address format
        
        Args:
            ip: IP address string to validate
            
        Returns:
            True if valid IPv4 address, False otherwise
        """
        if not ip or not isinstance(ip, str):
            return False
        
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False