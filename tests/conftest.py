"""
Pytest fixtures for Barcode Central tests
"""
import os
import pytest
import tempfile
import shutil
from app import app as flask_app


@pytest.fixture
def app():
    """Create and configure a test Flask application instance"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Create temporary directories for testing
    test_dir = tempfile.mkdtemp()
    flask_app.config['TEST_DIR'] = test_dir
    
    yield flask_app
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


@pytest.fixture
def client(app):
    """Create a test client for the Flask application"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create an authenticated test client"""
    # Login with default credentials
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    })
    return client


@pytest.fixture
def sample_template():
    """Sample template data for testing"""
    return {
        'filename': 'test_template.zpl.j2',
        'content': '^XA\n^FO50,50^FD{{ text }}^FS\n^XZ',
        'metadata': {
            'name': 'Test Template',
            'description': 'A test template',
            'size': '4x6',
            'variables': ['text'],
            'created': '2024-01-15T10:00:00',
            'modified': '2024-01-15T10:00:00'
        }
    }


@pytest.fixture
def sample_template_with_multiple_vars():
    """Sample template with multiple variables"""
    return {
        'filename': 'multi_var_template.zpl.j2',
        'content': '^XA\n^FO50,50^FD{{ name }}^FS\n^FO50,100^FD{{ address }}^FS\n^FO50,150^FD{{ city }}^FS\n^XZ',
        'metadata': {
            'name': 'Multi Variable Template',
            'description': 'Template with multiple variables',
            'size': '4x6',
            'variables': ['name', 'address', 'city'],
            'created': '2024-01-15T10:00:00',
            'modified': '2024-01-15T10:00:00'
        }
    }


@pytest.fixture
def sample_printer():
    """Sample printer data for testing"""
    return {
        'id': 'test-printer-001',
        'name': 'Test Printer',
        'ip': '192.168.1.100',
        'port': 9100,
        'supported_sizes': ['4x6', '4x2'],
        'dpi': 203,
        'enabled': True,
        'description': 'Test printer for unit tests'
    }


@pytest.fixture
def sample_printer_disabled():
    """Sample disabled printer for testing"""
    return {
        'id': 'test-printer-002',
        'name': 'Disabled Printer',
        'ip': '192.168.1.101',
        'port': 9100,
        'supported_sizes': ['4x6'],
        'dpi': 203,
        'enabled': False,
        'description': 'Disabled test printer'
    }


@pytest.fixture
def sample_print_job():
    """Sample print job data for testing"""
    return {
        'template': 'test_template.zpl.j2',
        'printer_id': 'test-printer-001',
        'variables': {
            'text': 'Test Label'
        },
        'copies': 1
    }


@pytest.fixture
def sample_history_entry():
    """Sample history entry for testing"""
    return {
        'id': 'hist-001',
        'timestamp': '2024-01-15T10:30:00',
        'template': 'test_template.zpl.j2',
        'printer_id': 'test-printer-001',
        'printer_name': 'Test Printer',
        'variables': {
            'text': 'Test Label'
        },
        'copies': 1,
        'status': 'success',
        'zpl_content': '^XA\n^FO50,50^FDTest Label^FS\n^XZ'
    }


@pytest.fixture
def mock_labelary_response():
    """Mock response from Labelary API"""
    # Return a simple 1x1 PNG (smallest valid PNG)
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


@pytest.fixture
def temp_templates_dir(tmp_path):
    """Create a temporary templates directory"""
    templates_dir = tmp_path / "templates_zpl"
    templates_dir.mkdir()
    return templates_dir


@pytest.fixture
def temp_previews_dir(tmp_path):
    """Create a temporary previews directory"""
    previews_dir = tmp_path / "previews"
    previews_dir.mkdir()
    return previews_dir


@pytest.fixture
def temp_data_file(tmp_path):
    """Create a temporary JSON data file"""
    data_file = tmp_path / "test_data.json"
    return str(data_file)