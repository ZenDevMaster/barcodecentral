"""
Unit tests for utility functions
"""
import pytest
import os
import json
import tempfile
from utils.json_storage import read_json, write_json, append_to_json_array
from utils.validators import (
    validate_template_name,
    validate_printer_name,
    validate_label_size,
    validate_zpl_content,
    sanitize_filename
)


class TestJsonStorage:
    """Tests for JSON storage utilities"""
    
    def test_read_json_existing_file(self, temp_data_file):
        """Test reading an existing JSON file"""
        test_data = {'key': 'value', 'number': 42}
        with open(temp_data_file, 'w') as f:
            json.dump(test_data, f)
        
        result = read_json(temp_data_file)
        assert result == test_data
    
    def test_read_json_nonexistent_file(self, temp_data_file):
        """Test reading a non-existent file returns default"""
        result = read_json(temp_data_file + '_nonexistent')
        assert result == {}
    
    def test_read_json_custom_default(self, temp_data_file):
        """Test reading with custom default value"""
        result = read_json(temp_data_file + '_nonexistent', default=[])
        assert result == []
    
    def test_read_json_invalid_json(self, temp_data_file):
        """Test reading invalid JSON returns default"""
        with open(temp_data_file, 'w') as f:
            f.write('invalid json {')
        
        result = read_json(temp_data_file)
        assert result == {}
    
    def test_write_json_success(self, temp_data_file):
        """Test writing JSON data successfully"""
        test_data = {'key': 'value', 'list': [1, 2, 3]}
        result = write_json(temp_data_file, test_data)
        
        assert result is True
        assert os.path.exists(temp_data_file)
        
        # Verify content
        with open(temp_data_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_data
    
    def test_write_json_creates_directory(self, tmp_path):
        """Test that write_json creates parent directories"""
        nested_path = tmp_path / "subdir" / "data.json"
        test_data = {'test': 'data'}
        
        result = write_json(str(nested_path), test_data)
        assert result is True
        assert nested_path.exists()
    
    def test_append_to_json_array_new_file(self, temp_data_file):
        """Test appending to a new JSON array file"""
        item = {'id': 1, 'name': 'test'}
        result = append_to_json_array(temp_data_file, item)
        
        assert result is True
        data = read_json(temp_data_file)
        assert len(data) == 1
        assert data[0]['id'] == 1
        assert 'timestamp' in data[0]
    
    def test_append_to_json_array_existing_file(self, temp_data_file):
        """Test appending to an existing JSON array"""
        # Create initial data
        initial_data = [{'id': 1}]
        write_json(temp_data_file, initial_data)
        
        # Append new item
        new_item = {'id': 2}
        result = append_to_json_array(temp_data_file, new_item)
        
        assert result is True
        data = read_json(temp_data_file)
        assert len(data) == 2
        assert data[1]['id'] == 2
    
    def test_append_to_json_array_rotation(self, temp_data_file):
        """Test that array rotation works correctly"""
        # Add items up to max_items
        for i in range(15):
            append_to_json_array(temp_data_file, {'id': i}, max_items=10)
        
        data = read_json(temp_data_file)
        assert len(data) == 10
        # Should keep the last 10 items (5-14)
        assert data[0]['id'] == 5
        assert data[-1]['id'] == 14
    
    def test_append_to_json_array_with_timestamp(self, temp_data_file):
        """Test that timestamp is added if not present"""
        item = {'id': 1}
        append_to_json_array(temp_data_file, item)
        
        data = read_json(temp_data_file)
        assert 'timestamp' in data[0]
    
    def test_append_to_json_array_preserves_timestamp(self, temp_data_file):
        """Test that existing timestamp is preserved"""
        custom_timestamp = '2024-01-15T10:00:00Z'
        item = {'id': 1, 'timestamp': custom_timestamp}
        append_to_json_array(temp_data_file, item)
        
        data = read_json(temp_data_file)
        assert data[0]['timestamp'] == custom_timestamp


class TestValidators:
    """Tests for validation functions"""
    
    # Template name validation tests
    def test_validate_template_name_valid(self):
        """Test valid template names"""
        valid_names = [
            'template1',
            'my_template',
            'my-template',
            'Template 123',
            'test_template_v2'
        ]
        for name in valid_names:
            is_valid, error = validate_template_name(name)
            assert is_valid, f"'{name}' should be valid but got error: {error}"
    
    def test_validate_template_name_empty(self):
        """Test empty template name"""
        is_valid, error = validate_template_name('')
        assert not is_valid
        assert 'empty' in error.lower()
    
    def test_validate_template_name_too_long(self):
        """Test template name that's too long"""
        long_name = 'a' * 101
        is_valid, error = validate_template_name(long_name)
        assert not is_valid
        assert 'too long' in error.lower()
    
    def test_validate_template_name_invalid_chars(self):
        """Test template name with invalid characters"""
        invalid_names = [
            'template@123',
            'template#test',
            'template/path',
            'template\\path',
            'template$var'
        ]
        for name in invalid_names:
            is_valid, error = validate_template_name(name)
            assert not is_valid, f"'{name}' should be invalid"
    
    # Printer name validation tests
    def test_validate_printer_name_valid(self):
        """Test valid printer names"""
        valid_names = [
            'Printer1',
            'Office_Printer',
            'Warehouse-Printer',
            'Printer 123'
        ]
        for name in valid_names:
            is_valid, error = validate_printer_name(name)
            assert is_valid, f"'{name}' should be valid but got error: {error}"
    
    def test_validate_printer_name_empty(self):
        """Test empty printer name"""
        is_valid, error = validate_printer_name('')
        assert not is_valid
        assert 'empty' in error.lower()
    
    # Label size validation tests
    def test_validate_label_size_valid(self):
        """Test valid label sizes"""
        valid_sizes = [
            '4x6',
            '4x2',
            '2x1',
            '4.5x6.5',
            '3.5x5'
        ]
        for size in valid_sizes:
            is_valid, error = validate_label_size(size)
            assert is_valid, f"'{size}' should be valid but got error: {error}"
    
    def test_validate_label_size_empty(self):
        """Test empty label size"""
        is_valid, error = validate_label_size('')
        assert not is_valid
        assert 'empty' in error.lower()
    
    def test_validate_label_size_invalid_format(self):
        """Test invalid label size formats"""
        invalid_sizes = [
            '4',
            '4x',
            'x6',
            '4-6',
            '4*6',
            'abc',
            '4x6x2'
        ]
        for size in invalid_sizes:
            is_valid, error = validate_label_size(size)
            assert not is_valid, f"'{size}' should be invalid"
    
    def test_validate_label_size_out_of_range(self):
        """Test label sizes out of valid range"""
        invalid_sizes = [
            '0x6',
            '4x0',
            '13x6',
            '4x13',
            '-1x6'
        ]
        for size in invalid_sizes:
            is_valid, error = validate_label_size(size)
            assert not is_valid, f"'{size}' should be invalid (out of range)"
    
    # ZPL content validation tests
    def test_validate_zpl_content_valid(self):
        """Test valid ZPL content"""
        valid_zpl = [
            '^XA^FO50,50^FDTest^FS^XZ',
            '^XA\n^FO50,50^FDTest^FS\n^XZ',
            '^xa^fo50,50^fdtest^fs^xz',  # lowercase
        ]
        for zpl in valid_zpl:
            is_valid, error = validate_zpl_content(zpl)
            assert is_valid, f"ZPL should be valid but got error: {error}"
    
    def test_validate_zpl_content_empty(self):
        """Test empty ZPL content"""
        is_valid, error = validate_zpl_content('')
        assert not is_valid
        assert 'empty' in error.lower()
    
    def test_validate_zpl_content_missing_xa(self):
        """Test ZPL without ^XA"""
        is_valid, error = validate_zpl_content('^FO50,50^FDTest^FS^XZ')
        assert not is_valid
        assert '^XA' in error
    
    def test_validate_zpl_content_missing_xz(self):
        """Test ZPL without ^XZ"""
        is_valid, error = validate_zpl_content('^XA^FO50,50^FDTest^FS')
        assert not is_valid
        assert '^XZ' in error
    
    def test_validate_zpl_content_unbalanced(self):
        """Test ZPL with unbalanced ^XA and ^XZ"""
        is_valid, error = validate_zpl_content('^XA^XA^FO50,50^FDTest^FS^XZ')
        assert not is_valid
        assert 'unbalanced' in error.lower()
    
    def test_validate_zpl_content_too_large(self):
        """Test ZPL content that's too large"""
        large_zpl = '^XA' + ('A' * 100000) + '^XZ'
        is_valid, error = validate_zpl_content(large_zpl)
        assert not is_valid
        assert 'too large' in error.lower()
    
    # Filename sanitization tests
    def test_sanitize_filename_valid(self):
        """Test sanitizing valid filenames"""
        assert sanitize_filename('test.txt') == 'test.txt'
        assert sanitize_filename('my_file-123.json') == 'my_file-123.json'
    
    def test_sanitize_filename_invalid_chars(self):
        """Test sanitizing filenames with invalid characters"""
        assert sanitize_filename('test/file.txt') == 'test_file.txt'
        assert sanitize_filename('test\\file.txt') == 'test_file.txt'
        assert sanitize_filename('test:file.txt') == 'test_file.txt'
        assert sanitize_filename('test*file?.txt') == 'test_file_.txt'
    
    def test_sanitize_filename_empty(self):
        """Test sanitizing empty filename"""
        assert sanitize_filename('') == 'unnamed'
        assert sanitize_filename(None) == 'unnamed'
    
    def test_sanitize_filename_spaces(self):
        """Test sanitizing filenames with spaces"""
        assert sanitize_filename('  test.txt  ') == 'test.txt'
        assert sanitize_filename('my file.txt') == 'my_file.txt'
    
    def test_sanitize_filename_dots(self):
        """Test sanitizing filenames with leading/trailing dots"""
        assert sanitize_filename('.test.txt') == 'test.txt'
        assert sanitize_filename('test.txt.') == 'test.txt'
    
    def test_sanitize_filename_multiple_underscores(self):
        """Test collapsing multiple underscores"""
        assert sanitize_filename('test___file.txt') == 'test_file.txt'
    
    def test_sanitize_filename_too_long(self):
        """Test truncating long filenames"""
        long_name = 'a' * 250 + '.txt'
        result = sanitize_filename(long_name)
        assert len(result) <= 200
        assert result.endswith('.txt')
    
    def test_sanitize_filename_only_invalid_chars(self):
        """Test filename with only invalid characters"""
        assert sanitize_filename('///') == 'unnamed'
        assert sanitize_filename('***') == 'unnamed'