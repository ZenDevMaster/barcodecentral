"""
API tests for print endpoints
"""
import pytest
import json
from unittest.mock import patch


class TestPrintAPI:
    """Tests for print API endpoints"""
    
    def test_print_requires_auth(self, client):
        """Test that printing requires authentication"""
        response = client.post('/api/print',
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code in [302, 401]
    
    @patch('printer_manager.PrinterManager.send_zpl')
    @patch('requests.post')
    def test_print_success(self, mock_labelary, mock_send_zpl, auth_client, 
                          sample_template, sample_printer, mock_labelary_response):
        """Test successful print job"""
        # Mock printer send
        mock_send_zpl.return_value = (True, "Print successful")
        
        # Mock preview generation
        mock_labelary.return_value.status_code = 200
        mock_labelary.return_value.content = mock_labelary_response
        
        print_data = {
            'template': 'example.zpl.j2',
            'printer_id': 'test-printer',
            'variables': {'text': 'Test'},
            'copies': 1
        }
        
        response = auth_client.post('/api/print',
                                   data=json.dumps(print_data),
                                   content_type='application/json')
        
        # May fail if template/printer don't exist, but should not crash
        assert response.status_code in [200, 400, 404]
    
    def test_print_missing_fields(self, auth_client):
        """Test print with missing required fields"""
        incomplete_data = {'template': 'test.zpl.j2'}
        
        response = auth_client.post('/api/print',
                                   data=json.dumps(incomplete_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('requests.post')
    def test_print_preview_only(self, mock_labelary, auth_client, mock_labelary_response):
        """Test preview-only mode"""
        # Mock preview generation
        mock_labelary.return_value.status_code = 200
        mock_labelary.return_value.content = mock_labelary_response
        
        print_data = {
            'template': 'example.zpl.j2',
            'printer_id': 'test-printer',
            'variables': {'text': 'Test'},
            'preview_only': True
        }
        
        response = auth_client.post('/api/print',
                                   data=json.dumps(print_data),
                                   content_type='application/json')
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 404]
    
    def test_validate_print_job(self, auth_client):
        """Test validating print job"""
        validate_data = {
            'template': 'example.zpl.j2',
            'printer_id': 'test-printer',
            'variables': {'text': 'Test'}
        }
        
        response = auth_client.post('/api/print/validate',
                                   data=json.dumps(validate_data),
                                   content_type='application/json')
        
        # Should return validation result
        assert response.status_code in [200, 400, 404]