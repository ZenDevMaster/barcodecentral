"""
API tests for preview endpoints
"""
import pytest
import json
from unittest.mock import patch


class TestPreviewAPI:
    """Tests for preview API endpoints"""
    
    def test_generate_preview_requires_auth(self, client):
        """Test that generating preview requires authentication"""
        response = client.post('/api/preview/generate',
                              data=json.dumps({'zpl': '^XA^XZ'}),
                              content_type='application/json')
        assert response.status_code in [302, 401]
    
    @patch('requests.post')
    def test_generate_preview_success(self, mock_post, auth_client, mock_labelary_response):
        """Test generating preview successfully"""
        # Mock Labelary API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = mock_labelary_response
        
        preview_data = {
            'zpl': '^XA\n^FO50,50^FDTest^FS\n^XZ',
            'label_size': '4x6',
            'dpi': 203
        }
        
        response = auth_client.post('/api/preview/generate',
                                   data=json.dumps(preview_data),
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'preview_url' in data['data']
    
    def test_generate_preview_missing_zpl(self, auth_client):
        """Test generating preview without ZPL"""
        response = auth_client.post('/api/preview/generate',
                                   data=json.dumps({}),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_cleanup_previews_requires_auth(self, client):
        """Test that cleanup requires authentication"""
        response = client.post('/api/preview/cleanup')
        assert response.status_code in [302, 401]
    
    def test_cleanup_previews_success(self, auth_client):
        """Test cleaning up old previews"""
        response = auth_client.post('/api/preview/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True