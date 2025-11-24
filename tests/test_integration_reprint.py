"""
Integration tests for reprint workflow
"""
import pytest
import json
from unittest.mock import patch


@pytest.mark.integration
class TestReprintWorkflow:
    """Integration tests for reprint from history"""
    
    @pytest.fixture
    def setup_history_entry(self, auth_client):
        """Setup a history entry for reprint testing"""
        # Create template and printer
        template_data = {
            'filename': 'reprint_test.zpl.j2',
            'content': '^XA\n^FO50,50^FD{{ text }}^FS\n^XZ',
            'metadata': {'name': 'Reprint Test', 'size': '4x6'}
        }
        auth_client.post('/api/templates',
                        data=json.dumps(template_data),
                        content_type='application/json')
        
        printer_data = {
            'id': 'reprint-test-printer',
            'name': 'Reprint Test Printer',
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
    def test_reprint_from_history(self, mock_labelary, mock_send_zpl,
                                  auth_client, setup_history_entry, mock_labelary_response):
        """Test reprinting a label from history"""
        # Mock external services
        mock_labelary.return_value.status_code = 200
        mock_labelary.return_value.content = mock_labelary_response
        mock_send_zpl.return_value = (True, "Print successful")
        
        # Step 1: Create initial print job
        print_data = {
            'template': setup_history_entry['template'],
            'printer_id': setup_history_entry['printer_id'],
            'variables': {'text': 'Original Print'},
            'copies': 1
        }
        print_response = auth_client.post('/api/print',
                                         data=json.dumps(print_data),
                                         content_type='application/json')
        assert print_response.status_code == 200
        
        # Step 2: Get history entry
        history_response = auth_client.get('/api/history?limit=1')
        assert history_response.status_code == 200
        history_data = json.loads(history_response.data)
        
        if history_data['data']['total'] > 0:
            entry = history_data['data']['entries'][0]
            entry_id = entry['id']
            
            # Step 3: Load history entry details
            entry_response = auth_client.get(f'/api/history/{entry_id}')
            assert entry_response.status_code == 200
            entry_details = json.loads(entry_response.data)
            
            # Step 4: Reprint with same variables
            reprint_data = {
                'template': entry_details['data']['entry']['template'],
                'printer_id': entry_details['data']['entry']['printer_id'],
                'variables': entry_details['data']['entry']['variables'],
                'copies': 1
            }
            reprint_response = auth_client.post('/api/print',
                                               data=json.dumps(reprint_data),
                                               content_type='application/json')
            assert reprint_response.status_code == 200
            
            # Step 5: Verify new history entry created
            new_history_response = auth_client.get('/api/history?limit=2')
            new_history_data = json.loads(new_history_response.data)
            assert new_history_data['data']['total'] >= 2
    
    @patch('printer_manager.PrinterManager.send_zpl')
    @patch('requests.post')
    def test_reprint_with_modified_variables(self, mock_labelary, mock_send_zpl,
                                             auth_client, setup_history_entry, 
                                             mock_labelary_response):
        """Test reprinting with modified variables"""
        # Mock external services
        mock_labelary.return_value.status_code = 200
        mock_labelary.return_value.content = mock_labelary_response
        mock_send_zpl.return_value = (True, "Print successful")
        
        # Create initial print
        print_data = {
            'template': setup_history_entry['template'],
            'printer_id': setup_history_entry['printer_id'],
            'variables': {'text': 'Original'},
            'copies': 1
        }
        auth_client.post('/api/print',
                        data=json.dumps(print_data),
                        content_type='application/json')
        
        # Get history entry
        history_response = auth_client.get('/api/history?limit=1')
        history_data = json.loads(history_response.data)
        
        if history_data['data']['total'] > 0:
            entry = history_data['data']['entries'][0]
            
            # Reprint with modified variables
            modified_data = {
                'template': entry['template'],
                'printer_id': entry['printer_id'],
                'variables': {'text': 'Modified Text'},  # Changed
                'copies': 1
            }
            reprint_response = auth_client.post('/api/print',
                                               data=json.dumps(modified_data),
                                               content_type='application/json')
            assert reprint_response.status_code == 200
    
    def test_search_and_reprint(self, auth_client, setup_history_entry):
        """Test searching history and reprinting"""
        # Search for specific entry
        search_response = auth_client.get('/api/history/search?q=test')
        assert search_response.status_code == 200
        
        search_data = json.loads(search_response.data)
        assert 'results' in search_data['data']
        
        # If results found, could reprint (tested in other tests)
        # This test verifies search functionality works