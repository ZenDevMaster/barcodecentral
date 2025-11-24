"""
Unit tests for TemplateManager
"""
import pytest
import os
import tempfile
import shutil
from template_manager import TemplateManager
from jinja2 import TemplateError


class TestTemplateManager:
    """Tests for TemplateManager class"""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary templates directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_templates_dir):
        """Create a TemplateManager instance with temp directory"""
        return TemplateManager(templates_dir=temp_templates_dir)
    
    @pytest.fixture
    def sample_zpl_content(self):
        """Sample valid ZPL content"""
        return '^XA\n^FO50,50^FD{{ text }}^FS\n^XZ'
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample template metadata"""
        return {
            'name': 'Test Template',
            'description': 'A test template',
            'size': '4x6'
        }
    
    # Initialization tests
    def test_init_creates_directory(self, temp_templates_dir):
        """Test that initialization creates templates directory"""
        new_dir = os.path.join(temp_templates_dir, 'new_templates')
        manager = TemplateManager(templates_dir=new_dir)
        assert os.path.exists(new_dir)
    
    def test_init_with_existing_directory(self, temp_templates_dir):
        """Test initialization with existing directory"""
        manager = TemplateManager(templates_dir=temp_templates_dir)
        assert manager.templates_dir == temp_templates_dir
    
    # List templates tests
    def test_list_templates_empty(self, manager):
        """Test listing templates in empty directory"""
        templates = manager.list_templates()
        assert templates == []
    
    def test_list_templates_with_files(self, manager, sample_zpl_content, sample_metadata):
        """Test listing templates with existing files"""
        # Create a template
        manager.create_template('test1.zpl.j2', sample_zpl_content, sample_metadata)
        manager.create_template('test2.zpl.j2', sample_zpl_content, sample_metadata)
        
        templates = manager.list_templates()
        assert len(templates) == 2
        assert any(t['filename'] == 'test1.zpl.j2' for t in templates)
        assert any(t['filename'] == 'test2.zpl.j2' for t in templates)
    
    def test_list_templates_sorted(self, manager, sample_zpl_content, sample_metadata):
        """Test that templates are sorted by filename"""
        manager.create_template('zebra.zpl.j2', sample_zpl_content, sample_metadata)
        manager.create_template('alpha.zpl.j2', sample_zpl_content, sample_metadata)
        
        templates = manager.list_templates()
        assert templates[0]['filename'] == 'alpha.zpl.j2'
        assert templates[1]['filename'] == 'zebra.zpl.j2'
    
    # Get template tests
    def test_get_template_success(self, manager, sample_zpl_content, sample_metadata):
        """Test getting an existing template"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        template = manager.get_template('test.zpl.j2')
        assert template['filename'] == 'test.zpl.j2'
        assert template['name'] == 'Test Template'
        assert template['size'] == '4x6'
        assert 'content' in template
        assert 'variables' in template
    
    def test_get_template_not_found(self, manager):
        """Test getting non-existent template raises error"""
        with pytest.raises(FileNotFoundError):
            manager.get_template('nonexistent.zpl.j2')
    
    def test_get_template_sanitizes_path(self, manager, sample_zpl_content, sample_metadata):
        """Test that get_template prevents directory traversal"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        # Try to access with path traversal
        template = manager.get_template('../test.zpl.j2')
        assert template['filename'] == 'test.zpl.j2'
    
    # Create template tests
    def test_create_template_success(self, manager, sample_zpl_content, sample_metadata):
        """Test creating a new template"""
        filepath = manager.create_template('new_template.zpl.j2', sample_zpl_content, sample_metadata)
        
        assert os.path.exists(filepath)
        assert 'new_template.zpl.j2' in filepath
    
    def test_create_template_without_extension(self, manager, sample_zpl_content, sample_metadata):
        """Test creating template adds .zpl.j2 extension"""
        with pytest.raises(ValueError, match="must end with '.zpl.j2'"):
            manager.create_template('template', sample_zpl_content, sample_metadata)
    
    def test_create_template_already_exists(self, manager, sample_zpl_content, sample_metadata):
        """Test creating duplicate template raises error"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        with pytest.raises(FileExistsError):
            manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
    
    def test_create_template_invalid_zpl(self, manager, sample_metadata):
        """Test creating template with invalid ZPL"""
        invalid_zpl = 'invalid zpl content'
        
        with pytest.raises(ValueError, match="Invalid ZPL content"):
            manager.create_template('test.zpl.j2', invalid_zpl, sample_metadata)
    
    def test_create_template_invalid_size(self, manager, sample_zpl_content):
        """Test creating template with invalid label size"""
        invalid_metadata = {
            'name': 'Test',
            'size': 'invalid'
        }
        
        with pytest.raises(ValueError, match="Invalid label size"):
            manager.create_template('test.zpl.j2', sample_zpl_content, invalid_metadata)
    
    def test_create_template_sanitizes_filename(self, manager, sample_zpl_content, sample_metadata):
        """Test that filename is sanitized"""
        filepath = manager.create_template('test/bad\\name.zpl.j2', sample_zpl_content, sample_metadata)
        
        # Should sanitize to safe filename
        assert 'test_bad_name.zpl.j2' in filepath or 'test_bad_name.zpl.j2.zpl.j2' in filepath
    
    # Update template tests
    def test_update_template_success(self, manager, sample_zpl_content, sample_metadata):
        """Test updating an existing template"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        new_content = '^XA\n^FO50,50^FD{{ updated }}^FS\n^XZ'
        new_metadata = {'name': 'Updated Template', 'size': '4x2'}
        
        filepath = manager.update_template('test.zpl.j2', new_content, new_metadata)
        assert os.path.exists(filepath)
        
        # Verify update
        template = manager.get_template('test.zpl.j2')
        assert template['name'] == 'Updated Template'
        assert 'updated' in template['variables']
    
    def test_update_template_not_found(self, manager, sample_zpl_content, sample_metadata):
        """Test updating non-existent template raises error"""
        with pytest.raises(FileNotFoundError):
            manager.update_template('nonexistent.zpl.j2', sample_zpl_content, sample_metadata)
    
    def test_update_template_invalid_zpl(self, manager, sample_zpl_content, sample_metadata):
        """Test updating with invalid ZPL"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        invalid_zpl = 'invalid content'
        with pytest.raises(ValueError, match="Invalid ZPL content"):
            manager.update_template('test.zpl.j2', invalid_zpl, sample_metadata)
    
    # Delete template tests
    def test_delete_template_success(self, manager, sample_zpl_content, sample_metadata):
        """Test deleting a template"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        result = manager.delete_template('test.zpl.j2')
        assert result is True
        
        # Verify deletion
        with pytest.raises(FileNotFoundError):
            manager.get_template('test.zpl.j2')
    
    def test_delete_template_not_found(self, manager):
        """Test deleting non-existent template raises error"""
        with pytest.raises(FileNotFoundError):
            manager.delete_template('nonexistent.zpl.j2')
    
    # Render template tests
    def test_render_template_success(self, manager, sample_zpl_content, sample_metadata):
        """Test rendering template with variables"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        rendered = manager.render_template('test.zpl.j2', {'text': 'Hello World'})
        assert 'Hello World' in rendered
        assert '^XA' in rendered
        assert '^XZ' in rendered
    
    def test_render_template_missing_variable(self, manager, sample_zpl_content, sample_metadata):
        """Test rendering without required variable raises error"""
        manager.create_template('test.zpl.j2', sample_zpl_content, sample_metadata)
        
        with pytest.raises(TemplateError, match="Missing required variable"):
            manager.render_template('test.zpl.j2', {})
    
    def test_render_template_not_found(self, manager):
        """Test rendering non-existent template raises error"""
        with pytest.raises(FileNotFoundError):
            manager.render_template('nonexistent.zpl.j2', {})
    
    def test_render_template_multiple_variables(self, manager, sample_metadata):
        """Test rendering template with multiple variables"""
        content = '^XA\n^FO50,50^FD{{ name }}^FS\n^FO50,100^FD{{ address }}^FS\n^XZ'
        manager.create_template('multi.zpl.j2', content, sample_metadata)
        
        rendered = manager.render_template('multi.zpl.j2', {
            'name': 'John Doe',
            'address': '123 Main St'
        })
        
        assert 'John Doe' in rendered
        assert '123 Main St' in rendered
    
    # Validate template tests
    def test_validate_template_valid(self, manager, sample_zpl_content):
        """Test validating valid template"""
        is_valid, error = manager.validate_template(sample_zpl_content)
        assert is_valid
        assert error is None
    
    def test_validate_template_invalid_zpl(self, manager):
        """Test validating invalid ZPL"""
        invalid_zpl = 'invalid content'
        is_valid, error = manager.validate_template(invalid_zpl)
        assert not is_valid
        assert error is not None
    
    def test_validate_template_invalid_jinja2(self, manager):
        """Test validating invalid Jinja2 syntax"""
        invalid_template = '^XA\n^FO50,50^FD{{ unclosed ^FS\n^XZ'
        is_valid, error = manager.validate_template(invalid_template)
        assert not is_valid
        assert 'syntax error' in error.lower()
    
    # Extract variables tests
    def test_extract_variables_single(self, manager, sample_zpl_content):
        """Test extracting single variable"""
        variables = manager.extract_variables(sample_zpl_content)
        assert variables == ['text']
    
    def test_extract_variables_multiple(self, manager):
        """Test extracting multiple variables"""
        content = '^XA\n^FO50,50^FD{{ name }}^FS\n^FO50,100^FD{{ address }}^FS\n^FO50,150^FD{{ city }}^FS\n^XZ'
        variables = manager.extract_variables(content)
        assert set(variables) == {'name', 'address', 'city'}
        assert variables == sorted(variables)  # Should be sorted
    
    def test_extract_variables_none(self, manager):
        """Test extracting variables from template with none"""
        content = '^XA\n^FO50,50^FDStatic Text^FS\n^XZ'
        variables = manager.extract_variables(content)
        assert variables == []
    
    def test_extract_variables_duplicate(self, manager):
        """Test that duplicate variables are listed once"""
        content = '^XA\n^FO50,50^FD{{ text }}^FS\n^FO50,100^FD{{ text }}^FS\n^XZ'
        variables = manager.extract_variables(content)
        assert variables == ['text']
    
    # Parse metadata tests
    def test_parse_metadata_complete(self, manager):
        """Test parsing complete metadata"""
        content = '''
^XA
^FX Template Metadata
^FX name: Test Template
^FX description: A test template
^FX size: 4x6
^FX variables: var1, var2, var3
^FX created: 2024-01-15
^FO50,50^FDTest^FS
^XZ
'''
        metadata = manager.parse_metadata(content)
        assert metadata['name'] == 'Test Template'
        assert metadata['description'] == 'A test template'
        assert metadata['size'] == '4x6'
        assert metadata['variables'] == ['var1', 'var2', 'var3']
        assert metadata['created'] == '2024-01-15'
    
    def test_parse_metadata_partial(self, manager):
        """Test parsing partial metadata"""
        content = '''
^XA
^FX Template Metadata
^FX name: Simple Template
^FO50,50^FDTest^FS
^XZ
'''
        metadata = manager.parse_metadata(content)
        assert metadata['name'] == 'Simple Template'
        assert 'description' not in metadata
    
    def test_parse_metadata_none(self, manager):
        """Test parsing template with no metadata"""
        content = '^XA\n^FO50,50^FDTest^FS\n^XZ'
        metadata = manager.parse_metadata(content)
        assert metadata == {}
    
    def test_parse_metadata_variables_list(self, manager):
        """Test that variables are parsed as list"""
        content = '^XA\n^FX variables: name, address, city\n^XZ'
        metadata = manager.parse_metadata(content)
        assert isinstance(metadata['variables'], list)
        assert len(metadata['variables']) == 3
    
    # Build template with metadata tests
    def test_build_template_with_metadata(self, manager, sample_zpl_content, sample_metadata):
        """Test building template with metadata header"""
        result = manager._build_template_with_metadata(sample_zpl_content, sample_metadata)
        
        assert '^FX Template Metadata' in result
        assert '^FX name: Test Template' in result
        assert '^FX size: 4x6' in result
        assert '^XA' in result
        assert '^XZ' in result
    
    def test_build_template_removes_existing_metadata(self, manager, sample_metadata):
        """Test that existing metadata is removed"""
        content_with_metadata = '''
^XA
^FX Template Metadata
^FX name: Old Name
^FX size: 2x1
^FO50,50^FDTest^FS
^XZ
'''
        result = manager._build_template_with_metadata(content_with_metadata, sample_metadata)
        
        # Should have new metadata
        assert '^FX name: Test Template' in result
        assert '^FX size: 4x6' in result
        
        # Should not have old metadata
        assert 'Old Name' not in result
        assert '2x1' not in result