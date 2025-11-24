"""
Integration tests for complete print workflow
"""
import pytest
import json
from unittest.mock import patch


@pytest.mark.integration
class TestPrintWorkflow:
    """Integration tests for complete print workflow"""
    
    @pytest.fixture
    def setup_test_data(self, auth_client):
        """Setup test template and printer"""
        # Create test template
        template_data = {
            'filename': 'integration_test.zpl.j2',
            'content': '^XA\n^FO50,50^FD{{ text }}^FS\n^XZ',
            'metadata': {
                'name': 'Integration Test Template',
                'size': '4x6'
            }
        }
        auth_client.post('/api/templates',
                        data=json.dumps(template_data),
                        content_type='application/json')
        
        # Create test printer
        printer_data = {
            'id': 'integration-test-printer',
            'name': 'Integration Test Printer',
            'ip': '192.168.1.100',
            'port': 9100,
            'supported_sizes': ['4x6'],
            'dpi': 203,
            'enabled': True
        }
        auth_client.post('/api/printers',
                        data=json.dumps(printer_data),
                        content_type='application/json')
        
        yield {
            'template': template_data['filename'],
            'printer_id': printer_data['id']
        }
        
        # Cleanup
        auth_client.delete(f'/api/templates/{template_data["filename"]}')
        auth_client.delete(f'/api/printers/{printer_data["id"]}')
    
    @patch('printer_manager.PrinterManager.send_zpl')
    @patch('requests.post')
    def test_complete_print_workflow(self, mock_labelary, mock_send_zpl, 
                                     auth_client, setup_test_data, mock_labelary_response):
        """Test complete print workflow from template to history"""
        # Mock external services
        mock_labelary.return_value.status_code = 200
        mock_labelary.return_value.content = mock_labelary_response
        mock_send_zpl.return_value = (True, "Print successful")
        
        # Step 1: Select template
        template_response = auth_client.get(f'/api/templates/{setup_test_data["template"]}')
        assert template_response.status_code == 200
        template_data = json.loads(template_response.data)
        assert template_data['success'] is True
        
        # Step 2: Render with variables
        render_data = {'variables': {'text': 'Integration Test'}}
        render_response = auth_client.post(
            f'/api/templates/{setup_test_data["template"]}/render',
            data=json.dumps(render_data),
            content_type='application/json'
        )
        assert render_response.status_code == 200
        rendered = json.loads(render_response.data)
        assert 'Integration Test' in rendered['data']['zpl']
        
        # Step 3: Generate preview
        preview_data = {
            'zpl': rendered['data']['zpl'],
            'label_size': '4x6',
            'dpi': 203
        }
        preview_response = auth_client.post('/api/preview/generate',
                                           data=json.dumps(preview_data),
                                           content_type='application/json')
        assert preview_response.status_code == 200
        
        # Step 4: Validate printer compatibility
        validate_data = {'label_size': '4x6'}
        validate_response = auth_client.post(
            f'/api/printers/{setup_test_data["printer_id"]}/validate',
            data=json.dumps(validate_data),
            content_type='application/json'
        )
        assert validate_response.status_code == 200
        
        # Step 5: Send to printer
        print_data = {
            'template': setup_test_data['template'],
            'printer_id': setup_test_data['printer_id'],
            'variables': {'text': 'Integration Test'},
            'copies': 1
        }
        print_response = auth_client.post('/api/print',
                                         data=json.dumps(print_data),
                                         content_type='application/json')
        assert print_response.status_code == 200
        print_result = json.loads(print_response.data)
        assert print_result['success'] is True
        
        # Step 6: Verify history entry
        history_response = auth_client.get('/api/history?limit=1')
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        assert history_data['data']['total'] > 0
    
    @patch('requests.post')
    def test_preview_only_workflow(self, mock_labelary, auth_client, 
                                   setup_test_data, mock_labelary_response):
        """Test preview-only workflow without printing"""
        # Mock preview generation
        mock_labelary.return_value.status_code = 200
        mock_labelary.return_value.content = mock_labelary_response
        
        # Render template
        render_data = {'variables': {'text': 'Preview Test'}}
        render_response = auth_client.post(
            f'/api/templates/{setup_test_data["template"]}/render',
            data=json.dumps(render_data),
            content_type='application/json'
        )
        assert render_response.status_code == 200
        rendered = json.loads(render_response.data)
        
        # Generate preview only
        preview_data = {
            'zpl': rendered['data']['zpl'],
            'label_size': '4x6',
            'dpi': 203
        }
        preview_response = auth_client.post('/api/preview/generate',
                                           data=json.dumps(preview_data),
                                           content_type='application/json')
        assert preview_response.status_code == 200
        preview_result = json.loads(preview_response.data)
        assert 'preview_url' in preview_result['data']
    
    def test_validation_workflow(self, auth_client, setup_test_data):
        """Test validation before printing"""
        # Validate template
        template_response = auth_client.get(f'/api/templates/{setup_test_data["template"]}')
        template_data = json.loads(template_response.data)
        
        validate_data = {'content': template_data['data']['template']['content']}
        validate_response = auth_client.post('/api/templates/validate',
                                            data=json.dumps(validate_data),
                                            content_type='application/json')
        assert validate_response.status_code == 200
        validate_result = json.loads(validate_response.data)
        assert validate_result['data']['valid'] is True
        
        # Validate printer compatibility
        compat_data = {'label_size': '4x6'}
        compat_response = auth_client.post(
            f'/api/printers/{setup_test_data["printer_id"]}/validate',
            data=json.dumps(compat_data),
            content_type='application/json'
        )
        assert compat_response.status_code == 200