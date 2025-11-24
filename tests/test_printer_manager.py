"""
Unit tests for PrinterManager
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from printer_manager import PrinterManager


class TestPrinterManager:
    """Tests for PrinterManager class"""
    
    @pytest.fixture
    def temp_printers_file(self, tmp_path):
        """Create a temporary printers file"""
        printers_file = tmp_path / "printers.json"
        return str(printers_file)
    
    @pytest.fixture
    def manager(self, temp_printers_file):
        """Create a PrinterManager instance with temp file"""
        return PrinterManager(printers_file=temp_printers_file)
    
    @pytest.fixture
    def valid_printer_data(self):
        """Valid printer configuration data"""
        return {
            'id': 'test-printer-001',
            'name': 'Test Printer',
            'ip': '192.168.1.100',
            'port': 9100,
            'supported_sizes': ['4x6', '4x2'],
            'dpi': 203,
            'enabled': True,
            'description': 'Test printer'
        }
    
    # Initialization tests
    def test_init_creates_manager(self, temp_printers_file):
        """Test that manager initializes correctly"""
        manager = PrinterManager(printers_file=temp_printers_file)
        assert manager.printers_file == temp_printers_file
        assert manager._printers_cache is None
    
    # List printers tests
    def test_list_printers_empty(self, manager):
        """Test listing printers when none exist"""
        printers = manager.list_printers()
        assert printers == []
    
    def test_list_printers_with_data(self, manager, valid_printer_data):
        """Test listing printers with existing data"""
        manager.add_printer(valid_printer_data)
        
        printers = manager.list_printers()
        assert len(printers) == 1
        assert printers[0]['id'] == 'test-printer-001'
    
    # Get printer tests
    def test_get_printer_success(self, manager, valid_printer_data):
        """Test getting an existing printer"""
        manager.add_printer(valid_printer_data)
        
        printer = manager.get_printer('test-printer-001')
        assert printer is not None
        assert printer['name'] == 'Test Printer'
        assert printer['ip'] == '192.168.1.100'
    
    def test_get_printer_not_found(self, manager):
        """Test getting non-existent printer returns None"""
        printer = manager.get_printer('nonexistent')
        assert printer is None
    
    # Add printer tests
    def test_add_printer_success(self, manager, valid_printer_data):
        """Test adding a valid printer"""
        success, message = manager.add_printer(valid_printer_data)
        
        assert success is True
        assert 'successfully' in message.lower()
        
        # Verify printer was added
        printer = manager.get_printer('test-printer-001')
        assert printer is not None
    
    def test_add_printer_missing_required_field(self, manager):
        """Test adding printer with missing required field"""
        incomplete_data = {
            'id': 'test',
            'name': 'Test'
            # Missing other required fields
        }
        
        success, message = manager.add_printer(incomplete_data)
        assert success is False
        assert 'missing required field' in message.lower()
    
    def test_add_printer_duplicate_id(self, manager, valid_printer_data):
        """Test adding printer with duplicate ID"""
        manager.add_printer(valid_printer_data)
        
        success, message = manager.add_printer(valid_printer_data)
        assert success is False
        assert 'already exists' in message.lower()
    
    def test_add_printer_invalid_id_format(self, manager, valid_printer_data):
        """Test adding printer with invalid ID format"""
        valid_printer_data['id'] = 'invalid@id!'
        
        success, message = manager.add_printer(valid_printer_data)
        assert success is False
        assert 'can only contain' in message.lower()
    
    def test_add_printer_invalid_ip(self, manager, valid_printer_data):
        """Test adding printer with invalid IP"""
        valid_printer_data['ip'] = 'invalid.ip'
        
        success, message = manager.add_printer(valid_printer_data)
        assert success is False
        assert 'invalid ip' in message.lower()
    
    def test_add_printer_invalid_port(self, manager, valid_printer_data):
        """Test adding printer with invalid port"""
        invalid_ports = [0, -1, 70000, 'abc']
        
        for port in invalid_ports:
            data = valid_printer_data.copy()
            data['id'] = f'test-{port}'
            data['port'] = port
            
            success, message = manager.add_printer(data)
            assert success is False
            assert 'port' in message.lower()
    
    def test_add_printer_invalid_supported_sizes(self, manager, valid_printer_data):
        """Test adding printer with invalid supported sizes"""
        valid_printer_data['supported_sizes'] = []
        
        success, message = manager.add_printer(valid_printer_data)
        assert success is False
        assert 'non-empty list' in message.lower()
    
    def test_add_printer_invalid_label_size(self, manager, valid_printer_data):
        """Test adding printer with invalid label size format"""
        valid_printer_data['supported_sizes'] = ['invalid']
        
        success, message = manager.add_printer(valid_printer_data)
        assert success is False
        assert 'invalid label size' in message.lower()
    
    def test_add_printer_invalid_dpi(self, manager, valid_printer_data):
        """Test adding printer with invalid DPI"""
        valid_printer_data['dpi'] = -1
        
        success, message = manager.add_printer(valid_printer_data)
        assert success is False
        assert 'dpi' in message.lower()
    
    def test_add_printer_default_enabled(self, manager, valid_printer_data):
        """Test that enabled defaults to True"""
        del valid_printer_data['enabled']
        
        success, _ = manager.add_printer(valid_printer_data)
        assert success is True
        
        printer = manager.get_printer('test-printer-001')
        assert printer['enabled'] is True
    
    # Update printer tests
    def test_update_printer_success(self, manager, valid_printer_data):
        """Test updating an existing printer"""
        manager.add_printer(valid_printer_data)
        
        update_data = {
            'name': 'Updated Printer',
            'ip': '192.168.1.101'
        }
        
        success, message = manager.update_printer('test-printer-001', update_data)
        assert success is True
        
        # Verify update
        printer = manager.get_printer('test-printer-001')
        assert printer['name'] == 'Updated Printer'
        assert printer['ip'] == '192.168.1.101'
    
    def test_update_printer_not_found(self, manager):
        """Test updating non-existent printer"""
        success, message = manager.update_printer('nonexistent', {'name': 'Test'})
        assert success is False
        assert 'not found' in message.lower()
    
    def test_update_printer_invalid_ip(self, manager, valid_printer_data):
        """Test updating with invalid IP"""
        manager.add_printer(valid_printer_data)
        
        success, message = manager.update_printer('test-printer-001', {'ip': 'invalid'})
        assert success is False
        assert 'invalid ip' in message.lower()
    
    def test_update_printer_preserves_id(self, manager, valid_printer_data):
        """Test that update doesn't change printer ID"""
        manager.add_printer(valid_printer_data)
        
        # Try to change ID
        manager.update_printer('test-printer-001', {'id': 'different-id'})
        
        # ID should remain unchanged
        printer = manager.get_printer('test-printer-001')
        assert printer['id'] == 'test-printer-001'
    
    # Delete printer tests
    def test_delete_printer_success(self, manager, valid_printer_data):
        """Test deleting a printer"""
        manager.add_printer(valid_printer_data)
        
        success, message = manager.delete_printer('test-printer-001')
        assert success is True
        
        # Verify deletion
        printer = manager.get_printer('test-printer-001')
        assert printer is None
    
    def test_delete_printer_not_found(self, manager):
        """Test deleting non-existent printer"""
        success, message = manager.delete_printer('nonexistent')
        assert success is False
        assert 'not found' in message.lower()
    
    # Validate compatibility tests
    def test_validate_compatibility_success(self, manager, valid_printer_data):
        """Test validating compatible printer and label size"""
        manager.add_printer(valid_printer_data)
        
        is_compatible, message = manager.validate_printer_compatibility('test-printer-001', '4x6')
        assert is_compatible is True
        assert 'compatible' in message.lower()
    
    def test_validate_compatibility_printer_not_found(self, manager):
        """Test validating with non-existent printer"""
        is_compatible, message = manager.validate_printer_compatibility('nonexistent', '4x6')
        assert is_compatible is False
        assert 'not found' in message.lower()
    
    def test_validate_compatibility_printer_disabled(self, manager, valid_printer_data):
        """Test validating with disabled printer"""
        valid_printer_data['enabled'] = False
        manager.add_printer(valid_printer_data)
        
        is_compatible, message = manager.validate_printer_compatibility('test-printer-001', '4x6')
        assert is_compatible is False
        assert 'disabled' in message.lower()
    
    def test_validate_compatibility_unsupported_size(self, manager, valid_printer_data):
        """Test validating with unsupported label size"""
        manager.add_printer(valid_printer_data)
        
        is_compatible, message = manager.validate_printer_compatibility('test-printer-001', '8x10')
        assert is_compatible is False
        assert 'does not support' in message.lower()
    
    # Test printer connection tests (mocked)
    @patch('socket.socket')
    def test_connection_success(self, mock_socket, manager, valid_printer_data):
        """Test successful printer connection"""
        manager.add_printer(valid_printer_data)
        
        # Mock successful connection
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        
        success, message = manager.test_printer_connection('test-printer-001')
        assert success is True
        assert 'successful' in message.lower()
    
    @patch('socket.socket')
    def test_connection_timeout(self, mock_socket, manager, valid_printer_data):
        """Test printer connection timeout"""
        manager.add_printer(valid_printer_data)
        
        # Mock timeout
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect.side_effect = TimeoutError()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        
        success, message = manager.test_printer_connection('test-printer-001')
        assert success is False
        assert 'timed out' in message.lower() or 'timeout' in message.lower()
    
    @patch('socket.socket')
    def test_connection_error(self, mock_socket, manager, valid_printer_data):
        """Test printer connection error"""
        manager.add_printer(valid_printer_data)
        
        # Mock connection error
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect.side_effect = OSError("Connection refused")
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        
        success, message = manager.test_printer_connection('test-printer-001')
        assert success is False
    
    def test_connection_printer_not_found(self, manager):
        """Test connection test with non-existent printer"""
        success, message = manager.test_printer_connection('nonexistent')
        assert success is False
        assert 'not found' in message.lower()
    
    # Send ZPL tests (mocked)
    @patch('socket.socket')
    def test_send_zpl_success(self, mock_socket, manager, valid_printer_data):
        """Test sending ZPL to printer"""
        manager.add_printer(valid_printer_data)
        
        # Mock successful send
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        
        zpl_content = '^XA^FO50,50^FDTest^FS^XZ'
        success, message = manager.send_zpl(valid_printer_data['id'], zpl_content)
        
        assert success is True
        mock_sock_instance.sendall.assert_called_once()
    
    @patch('socket.socket')
    def test_send_zpl_connection_error(self, mock_socket, manager, valid_printer_data):
        """Test sending ZPL with connection error"""
        manager.add_printer(valid_printer_data)
        
        # Mock connection error
        mock_sock_instance = MagicMock()
        mock_sock_instance.sendall.side_effect = OSError("Connection error")
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        
        zpl_content = '^XA^FO50,50^FDTest^FS^XZ'
        success, message = manager.send_zpl(valid_printer_data['id'], zpl_content)
        
        assert success is False
    
    def test_send_zpl_printer_not_found(self, manager):
        """Test sending ZPL to non-existent printer"""
        zpl_content = '^XA^FO50,50^FDTest^FS^XZ'
        success, message = manager.send_zpl('nonexistent', zpl_content)
        
        assert success is False
        assert 'not found' in message.lower()
    
    # Cache tests
    def test_cache_invalidation_on_save(self, manager, valid_printer_data):
        """Test that cache is invalidated when printers are saved"""
        manager.add_printer(valid_printer_data)
        
        # Cache should be populated
        manager.list_printers()
        assert manager._printers_cache is not None
        
        # Add another printer
        printer2 = valid_printer_data.copy()
        printer2['id'] = 'test-printer-002'
        manager.add_printer(printer2)
        
        # Cache should be invalidated
        assert manager._printers_cache is None
    
    # IP validation tests
    def test_validate_ip_valid(self, manager):
        """Test IP validation with valid IPs"""
        valid_ips = [
            '192.168.1.1',
            '10.0.0.1',
            '172.16.0.1',
            '255.255.255.255'
        ]
        
        for ip in valid_ips:
            assert manager._validate_ip(ip) is True
    
    def test_validate_ip_invalid(self, manager):
        """Test IP validation with invalid IPs"""
        invalid_ips = [
            'invalid',
            '256.1.1.1',
            '1.1.1',
            '1.1.1.1.1',
            'abc.def.ghi.jkl'
        ]
        
        for ip in invalid_ips:
            assert manager._validate_ip(ip) is False