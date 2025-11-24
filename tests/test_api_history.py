"""
API tests for history endpoints
"""
import pytest
import json


class TestHistoryAPI:
    """Tests for history API endpoints"""
    
    def test_list_history_requires_auth(self, client):
        """Test that listing history requires authentication"""
        response = client.get('/api/history')
        assert response.status_code in [302, 401]
    
    def test_list_history_success(self, auth_client):
        """Test listing history entries"""
        response = auth_client.get('/api/history')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'entries' in data['data']
        assert 'total' in data['data']
    
    def test_list_history_pagination(self, auth_client):
        """Test history pagination"""
        response = auth_client.get('/api/history?limit=10&offset=0')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_list_history_filters(self, auth_client):
        """Test history filtering"""
        response = auth_client.get('/api/history?status=success&template=test.zpl.j2')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_get_history_entry_not_found(self, auth_client):
        """Test getting non-existent history entry"""
        response = auth_client.get('/api/history/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_delete_history_entry_not_found(self, auth_client):
        """Test deleting non-existent history entry"""
        response = auth_client.delete('/api/history/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_search_history_requires_auth(self, client):
        """Test that searching history requires authentication"""
        response = client.get('/api/history/search?q=test')
        assert response.status_code in [302, 401]
    
    def test_search_history_success(self, auth_client):
        """Test searching history"""
        response = auth_client.get('/api/history/search?q=test')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'results' in data['data']
    
    def test_get_statistics_requires_auth(self, client):
        """Test that getting statistics requires authentication"""
        response = client.get('/api/history/statistics')
        assert response.status_code in [302, 401]
    
    def test_get_statistics_success(self, auth_client):
        """Test getting history statistics"""
        response = auth_client.get('/api/history/statistics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'statistics' in data['data']
    
    def test_cleanup_history_requires_auth(self, client):
        """Test that cleanup requires authentication"""
        response = client.post('/api/history/cleanup',
                              data=json.dumps({'days': 30}),
                              content_type='application/json')
        assert response.status_code in [302, 401]
    
    def test_cleanup_history_success(self, auth_client):
        """Test cleaning up old history"""
        response = auth_client.post('/api/history/cleanup',
                                   data=json.dumps({'days': 30}),
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_export_history_requires_auth(self, client):
        """Test that export requires authentication"""
        response = client.get('/api/history/export')
        assert response.status_code in [302, 401]
    
    def test_export_history_success(self, auth_client):
        """Test exporting history"""
        response = auth_client.get('/api/history/export')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'export' in data['data']