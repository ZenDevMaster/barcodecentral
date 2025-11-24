"""
API tests for authentication endpoints
"""
import pytest


class TestAuthAPI:
    """Tests for authentication API endpoints"""
    
    def test_login_page_loads(self, client):
        """Test that login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_login_success(self, client):
        """Test successful login"""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to dashboard
        assert b'Dashboard' in response.data or b'dashboard' in response.data
    
    def test_login_failure_wrong_password(self, client):
        """Test login with wrong password"""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'invalid' in response.data
    
    def test_login_failure_wrong_username(self, client):
        """Test login with wrong username"""
        response = client.post('/login', data={
            'username': 'wronguser',
            'password': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'invalid' in response.data
    
    def test_login_failure_empty_credentials(self, client):
        """Test login with empty credentials"""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_logout(self, auth_client):
        """Test logout"""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # After logout, accessing protected route should redirect to login
        response = auth_client.get('/dashboard')
        assert response.status_code == 302 or b'login' in response.data.lower()
    
    def test_protected_route_requires_auth(self, client):
        """Test that protected routes require authentication"""
        response = client.get('/dashboard')
        # Should redirect to login
        assert response.status_code == 302
    
    def test_api_protected_route_requires_auth(self, client):
        """Test that API routes require authentication"""
        response = client.get('/api/templates')
        # Should return 401 or redirect
        assert response.status_code in [302, 401]
    
    def test_authenticated_access_to_dashboard(self, auth_client):
        """Test authenticated access to dashboard"""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200
    
    def test_authenticated_access_to_api(self, auth_client):
        """Test authenticated access to API"""
        response = auth_client.get('/api/templates')
        assert response.status_code == 200