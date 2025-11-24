"""
API tests for template endpoints
"""
import pytest
import json


class TestTemplatesAPI:
    """Tests for templates API endpoints"""
    
    @pytest.fixture
    def sample_template_data(self):
        """Sample template data for testing"""
        return {
            'filename': 'test_api_template.zpl.j2',
            'content': '^XA\n^FO50,50^FD{{ text }}^FS\n^XZ',
            'metadata': {
                'name': 'API Test Template',
                'description': 'Template for API testing',
                'size': '4x6'
            }
        }
    
    # List templates tests
    def test_list_templates_requires_auth(self, client):
        """Test that listing templates requires authentication"""
        response = client.get('/api/templates')
        assert response.status_code in [302, 401]
    
    def test_list_templates_success(self, auth_client):
        """Test listing templates"""
        response = auth_client.get('/api/templates')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'templates' in data['data']
        assert 'count' in data['data']
    
    def test_list_templates_without_content(self, auth_client):
        """Test that templates list excludes content by default"""
        response = auth_client.get('/api/templates')
        data = json.loads(response.data)
        
        if data['data']['count'] > 0:
            template = data['data']['templates'][0]
            assert 'content' not in template
    
    def test_list_templates_with_content(self, auth_client):
        """Test listing templates with content included"""
        response = auth_client.get('/api/templates?include_content=true')
        data = json.loads(response.data)
        
        if data['data']['count'] > 0:
            template = data['data']['templates'][0]
            assert 'content' in template
    
    # Get template tests
    def test_get_template_requires_auth(self, client):
        """Test that getting template requires authentication"""
        response = client.get('/api/templates/example.zpl.j2')
        assert response.status_code in [302, 401]
    
    def test_get_template_success(self, auth_client):
        """Test getting a specific template"""
        # First, list templates to get a valid filename
        list_response = auth_client.get('/api/templates')
        list_data = json.loads(list_response.data)
        
        if list_data['data']['count'] > 0:
            filename = list_data['data']['templates'][0]['filename']
            
            response = auth_client.get(f'/api/templates/{filename}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'template' in data['data']
            assert data['data']['template']['filename'] == filename
            assert 'content' in data['data']['template']
    
    def test_get_template_not_found(self, auth_client):
        """Test getting non-existent template"""
        response = auth_client.get('/api/templates/nonexistent.zpl.j2')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
    
    # Create template tests
    def test_create_template_requires_auth(self, client, sample_template_data):
        """Test that creating template requires authentication"""
        response = client.post('/api/templates',
                              data=json.dumps(sample_template_data),
                              content_type='application/json')
        assert response.status_code in [302, 401]
    
    def test_create_template_success(self, auth_client, sample_template_data):
        """Test creating a new template"""
        response = auth_client.post('/api/templates',
                                   data=json.dumps(sample_template_data),
                                   content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Cleanup
        auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')
    
    def test_create_template_missing_fields(self, auth_client):
        """Test creating template with missing required fields"""
        incomplete_data = {
            'filename': 'incomplete.zpl.j2'
            # Missing content and metadata
        }
        
        response = auth_client.post('/api/templates',
                                   data=json.dumps(incomplete_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_create_template_invalid_zpl(self, auth_client):
        """Test creating template with invalid ZPL"""
        invalid_data = {
            'filename': 'invalid.zpl.j2',
            'content': 'invalid zpl content',
            'metadata': {'name': 'Invalid', 'size': '4x6'}
        }
        
        response = auth_client.post('/api/templates',
                                   data=json.dumps(invalid_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_create_template_duplicate(self, auth_client, sample_template_data):
        """Test creating duplicate template"""
        # Create first template
        auth_client.post('/api/templates',
                        data=json.dumps(sample_template_data),
                        content_type='application/json')
        
        # Try to create duplicate
        response = auth_client.post('/api/templates',
                                   data=json.dumps(sample_template_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        
        # Cleanup
        auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')
    
    # Update template tests
    def test_update_template_requires_auth(self, client, sample_template_data):
        """Test that updating template requires authentication"""
        response = client.put('/api/templates/test.zpl.j2',
                             data=json.dumps(sample_template_data),
                             content_type='application/json')
        assert response.status_code in [302, 401]
    
    def test_update_template_success(self, auth_client, sample_template_data):
        """Test updating an existing template"""
        # Create template first
        auth_client.post('/api/templates',
                        data=json.dumps(sample_template_data),
                        content_type='application/json')
        
        # Update template
        updated_data = sample_template_data.copy()
        updated_data['content'] = '^XA\n^FO50,50^FD{{ updated }}^FS\n^XZ'
        updated_data['metadata']['name'] = 'Updated Template'
        
        response = auth_client.put(f'/api/templates/{sample_template_data["filename"]}',
                                  data=json.dumps(updated_data),
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Cleanup
        auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')
    
    def test_update_template_not_found(self, auth_client, sample_template_data):
        """Test updating non-existent template"""
        response = auth_client.put('/api/templates/nonexistent.zpl.j2',
                                  data=json.dumps(sample_template_data),
                                  content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    # Delete template tests
    def test_delete_template_requires_auth(self, client):
        """Test that deleting template requires authentication"""
        response = client.delete('/api/templates/test.zpl.j2')
        assert response.status_code in [302, 401]
    
    def test_delete_template_success(self, auth_client, sample_template_data):
        """Test deleting a template"""
        # Create template first
        auth_client.post('/api/templates',
                        data=json.dumps(sample_template_data),
                        content_type='application/json')
        
        # Delete template
        response = auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_delete_template_not_found(self, auth_client):
        """Test deleting non-existent template"""
        response = auth_client.delete('/api/templates/nonexistent.zpl.j2')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    # Render template tests
    def test_render_template_requires_auth(self, client):
        """Test that rendering template requires authentication"""
        response = client.post('/api/templates/test.zpl.j2/render',
                              data=json.dumps({'variables': {}}),
                              content_type='application/json')
        assert response.status_code in [302, 401]
    
    def test_render_template_success(self, auth_client, sample_template_data):
        """Test rendering a template"""
        # Create template first
        auth_client.post('/api/templates',
                        data=json.dumps(sample_template_data),
                        content_type='application/json')
        
        # Render template
        render_data = {'variables': {'text': 'Hello World'}}
        response = auth_client.post(f'/api/templates/{sample_template_data["filename"]}/render',
                                   data=json.dumps(render_data),
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'zpl' in data['data']
        assert 'Hello World' in data['data']['zpl']
        
        # Cleanup
        auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')
    
    def test_render_template_missing_variable(self, auth_client, sample_template_data):
        """Test rendering template with missing variable"""
        # Create template first
        auth_client.post('/api/templates',
                        data=json.dumps(sample_template_data),
                        content_type='application/json')
        
        # Try to render without required variable
        render_data = {'variables': {}}
        response = auth_client.post(f'/api/templates/{sample_template_data["filename"]}/render',
                                   data=json.dumps(render_data),
                                   content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        
        # Cleanup
        auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')
    
    # Validate template tests
    def test_validate_template_requires_auth(self, client):
        """Test that validating template requires authentication"""
        response = client.post('/api/templates/test.zpl.j2/validate',
                              data=json.dumps({'content': '^XA^XZ'}),
                              content_type='application/json')
        assert response.status_code in [302, 401]
    
    def test_validate_template_valid(self, auth_client):
        """Test validating valid template content"""
        validate_data = {'content': '^XA\n^FO50,50^FD{{ text }}^FS\n^XZ'}
        response = auth_client.post('/api/templates/validate',
                                   data=json.dumps(validate_data),
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['valid'] is True
    
    def test_validate_template_invalid(self, auth_client):
        """Test validating invalid template content"""
        validate_data = {'content': 'invalid zpl'}
        response = auth_client.post('/api/templates/validate',
                                   data=json.dumps(validate_data),
                                   content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['valid'] is False
        assert 'error' in data['data']
    
    # Extract variables tests
    def test_extract_variables_requires_auth(self, client):
        """Test that extracting variables requires authentication"""
        response = client.get('/api/templates/test.zpl.j2/variables')
        assert response.status_code in [302, 401]
    
    def test_extract_variables_success(self, auth_client, sample_template_data):
        """Test extracting variables from template"""
        # Create template first
        auth_client.post('/api/templates',
                        data=json.dumps(sample_template_data),
                        content_type='application/json')
        
        # Extract variables
        response = auth_client.get(f'/api/templates/{sample_template_data["filename"]}/variables')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'variables' in data['data']
        assert 'text' in data['data']['variables']
        
        # Cleanup
        auth_client.delete(f'/api/templates/{sample_template_data["filename"]}')