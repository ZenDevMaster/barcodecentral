"""
API tests for printer endpoints
"""
import pytest
import json


class TestPrintersAPI:
    """Tests for printers API endpoints"""
    
    @pytest.fixture
    def sample_printer_data(self):
        """Sample printer data for testing"""
        return {
            'id': 'test-api-printer',
            'name': 'API Test Printer',
            'ip': '192.168.1.200',
            'port': 9100,
            'supported_sizes': ['4x6', '4x2'],
            'dpi': 203,
            'enabled': True,
            'description': 'Printer for API testing'
        }
    
    def test_list_printers_requires_auth(self, client):
        """Test that listing printers requires authentication"""
        response = client.get('/api/printers')
        assert response.status_code in [302, 401]
    
    def test_list_printers_success(self, auth_client):
        """Test listing printers"""
        response = auth_client.get('/api/printers')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'printers' in data['data']
    
    def test_get_printer_success(self, auth_client, sample_printer_data):
        """Test getting a specific printer"""
        # Add printer first
        auth_client.post('/api/printers',
                        data=json.dumps(sample_printer_data),
                        content_type='application/json')
        
        response = auth_client.get(f'/api/printers/{sample_printer_data["id"]}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['printer']['id'] == sample_printer_data['id']
        
        # Cleanup
        auth_client.delete(f'/api/printers/{sample_printer_data["id"]}')
    
    def test_get_printer_not_found(self, auth_client):
        """Test getting non-existent printer"""
        response = auth_client.get('/api/printers/nonexistent')
        assert response.status_code == 404
    
    def test_create_printer_success(self, auth_client, sample_printer_data):
        """Test creating a new printer"""
        response = auth_client.post('/api/printers',
                                   data=json.dumps(sample_printer_data),
                                   content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Cleanup
        auth_client.delete(f'/api/printers/{sample_printer_data["id"]}')
    
    def test_create_printer_invalid_data(self, auth_client):
        """Test creating printer with invalid data"""
        invalid_data = {'id': 'test', 'name': 'Test'}  # Missing required fields
        
        response = auth_client.post('/api/printers',
                                   data=json.dumps(invalid_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_update_printer_success(self, auth_client, sample_printer_data):
        """Test updating a printer"""
        # Create printer first
        auth_client.post('/api/printers',
                        data=json.dumps(sample_printer_data),
                        content_type='application/json')
        
        # Update printer
        update_data = {'name': 'Updated Printer Name'}
        response = auth_client.put(f'/api/printers/{sample_printer_data["id"]}',
                                  data=json.dumps(update_data),
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Cleanup
        auth_client.delete(f'/api/printers/{sample_printer_data["id"]}')
    
    def test_delete_printer_success(self, auth_client, sample_printer_data):
        """Test deleting a printer"""
        # Create printer first
        auth_client.post('/api/printers',
                        data=json.dumps(sample_printer_data),
                        content_type='application/json')
        
        # Delete printer
        response = auth_client.delete(f'/api/printers/{sample_printer_data["id"]}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_validate_compatibility_success(self, auth_client, sample_printer_data):
        """Test validating printer compatibility"""
        # Create printer first
        auth_client.post('/api/printers',
                        data=json.dumps(sample_printer_data),
                        content_type='application/json')
        
        # Validate compatibility
        validate_data = {'label_size': '4x6'}
        response = auth_client.post(f'/api/printers/{sample_printer_data["id"]}/validate',
                                   data=json.dumps(validate_data),
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Cleanup
        auth_client.delete(f'/api/printers/{sample_printer_data["id"]}')