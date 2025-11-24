"""
Template Manager for Barcode Central
Handles ZPL template CRUD operations, Jinja2 rendering, and validation
"""
import os
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, TemplateError, UndefinedError, StrictUndefined, meta

from utils.validators import validate_zpl_content, validate_label_size, validate_label_size_with_unit, sanitize_filename
from utils.label_size import LabelSize
from utils.unit_converter import Unit

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Manages ZPL templates with Jinja2 variable substitution
    """
    
    def __init__(self, templates_dir: str = 'templates_zpl'):
        """
        Initialize TemplateManager
        
        Args:
            templates_dir: Directory containing ZPL templates (default: 'templates_zpl')
        """
        self.templates_dir = templates_dir
        
        # Ensure templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Configure Jinja2 environment
        # Auto-escape disabled since ZPL is not HTML
        # Strict undefined behavior to catch missing variables
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.info(f"TemplateManager initialized with directory: {self.templates_dir}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available ZPL templates with metadata
        
        Returns:
            List of template dictionaries with metadata
        """
        templates = []
        
        try:
            # Scan directory for .zpl.j2 files
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.zpl.j2'):
                    try:
                        template_info = self.get_template(filename)
                        templates.append(template_info)
                    except Exception as e:
                        logger.error(f"Error loading template {filename}: {e}")
                        # Include template with error info
                        templates.append({
                            'filename': filename,
                            'name': filename,
                            'error': str(e)
                        })
            
            # Sort by filename
            templates.sort(key=lambda x: x.get('filename', ''))
            
            logger.info(f"Listed {len(templates)} templates")
            return templates
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def get_template(self, name: str) -> Dict[str, Any]:
        """
        Get specific template details and content
        
        Args:
            name: Template filename (e.g., 'shipping_label.zpl.j2')
            
        Returns:
            Dictionary with template metadata and content
            
        Raises:
            FileNotFoundError: If template doesn't exist
            ValueError: If template is invalid
        """
        # Sanitize filename to prevent directory traversal
        safe_name = os.path.basename(name)
        filepath = os.path.join(self.templates_dir, safe_name)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template '{name}' not found")
        
        # Read template content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Error reading template: {e}")
        
        # Parse metadata from template
        metadata = self.parse_metadata(content)
        
        # Get file stats
        stat = os.stat(filepath)
        created = datetime.fromtimestamp(stat.st_ctime).isoformat() + 'Z'
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat() + 'Z'
        
        # Extract variables from template
        variables = self.extract_variables(content)
        
        # Build response with backward compatibility
        result = {
            'filename': safe_name,
            'name': metadata.get('name', safe_name),
            'description': metadata.get('description', ''),
            'size': metadata.get('size', ''),  # Legacy format
            'variables': variables,
            'content': content,
            'created': metadata.get('created', created),
            'modified': metadata.get('modified', modified)
        }
        
        # Add new unit-aware fields if size is specified
        if metadata.get('size'):
            try:
                label_size = LabelSize.from_string(metadata['size'])
                result['size_unit'] = label_size.unit.value
                result['size_width'] = label_size.width
                result['size_height'] = label_size.height
                
                # Add convenience field for metric display
                width_mm, height_mm = label_size.to_mm()
                result['size_mm'] = f"{width_mm:.1f}x{height_mm:.1f}mm"
            except (ValueError, Exception) as e:
                # If parsing fails, fall back to legacy behavior
                logger.debug(f"Could not parse size as unit-aware: {e}")
        
        return result
    
    def create_template(self, name: str, content: str, metadata: Dict[str, Any]) -> str:
        """
        Create a new template file
        
        Args:
            name: Template filename (must end with .zpl.j2)
            content: ZPL template content
            metadata: Template metadata (name, description, size, etc.)
            
        Returns:
            Path to created template file
            
        Raises:
            ValueError: If template name or content is invalid
            FileExistsError: If template already exists
        """
        # Validate template name
        if not name.endswith('.zpl.j2'):
            raise ValueError("Template name must end with '.zpl.j2'")
        
        # Sanitize filename
        safe_name = sanitize_filename(name)
        if not safe_name.endswith('.zpl.j2'):
            safe_name += '.zpl.j2'
        
        filepath = os.path.join(self.templates_dir, safe_name)
        
        # Check if template already exists
        if os.path.exists(filepath):
            raise FileExistsError(f"Template '{safe_name}' already exists")
        
        # Validate ZPL content
        is_valid, error_msg = validate_zpl_content(content)
        if not is_valid:
            raise ValueError(f"Invalid ZPL content: {error_msg}")
        
        # Validate label size if provided (use new unit-aware validator)
        if 'size' in metadata:
            is_valid, error_msg, parsed_data = validate_label_size_with_unit(metadata['size'])
            if not is_valid:
                # Fall back to legacy validator for backward compatibility
                is_valid_legacy, error_msg_legacy = validate_label_size(metadata['size'])
                if not is_valid_legacy:
                    raise ValueError(f"Invalid label size: {error_msg}")
        
        # Build template content with metadata header
        template_content = self._build_template_with_metadata(content, metadata)
        
        # Write template file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info(f"Created template: {safe_name}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating template {safe_name}: {e}")
            raise ValueError(f"Error creating template: {e}")
    
    def update_template(self, name: str, content: str, metadata: Dict[str, Any]) -> str:
        """
        Update existing template
        
        Args:
            name: Template filename
            content: Updated ZPL template content
            metadata: Updated template metadata
            
        Returns:
            Path to updated template file
            
        Raises:
            FileNotFoundError: If template doesn't exist
            ValueError: If content is invalid
        """
        # Sanitize filename
        safe_name = os.path.basename(name)
        filepath = os.path.join(self.templates_dir, safe_name)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template '{name}' not found")
        
        # Validate ZPL content
        is_valid, error_msg = validate_zpl_content(content)
        if not is_valid:
            raise ValueError(f"Invalid ZPL content: {error_msg}")
        
        # Validate label size if provided (use new unit-aware validator)
        if 'size' in metadata:
            is_valid, error_msg, parsed_data = validate_label_size_with_unit(metadata['size'])
            if not is_valid:
                # Fall back to legacy validator for backward compatibility
                is_valid_legacy, error_msg_legacy = validate_label_size(metadata['size'])
                if not is_valid_legacy:
                    raise ValueError(f"Invalid label size: {error_msg}")
        
        # Update modified timestamp
        metadata['modified'] = datetime.utcnow().isoformat() + 'Z'
        
        # Build template content with metadata header
        template_content = self._build_template_with_metadata(content, metadata)
        
        # Write template file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info(f"Updated template: {safe_name}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error updating template {safe_name}: {e}")
            raise ValueError(f"Error updating template: {e}")
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template file
        
        Args:
            name: Template filename
            
        Returns:
            True if deleted successfully
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        # Sanitize filename
        safe_name = os.path.basename(name)
        filepath = os.path.join(self.templates_dir, safe_name)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template '{name}' not found")
        
        try:
            os.remove(filepath)
            logger.info(f"Deleted template: {safe_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template {safe_name}: {e}")
            raise ValueError(f"Error deleting template: {e}")
    
    def render_template(self, name: str, variables: Dict[str, Any]) -> str:
        """
        Render template with variables using Jinja2
        
        Args:
            name: Template filename
            variables: Dictionary of variables to substitute
            
        Returns:
            Rendered ZPL code
            
        Raises:
            FileNotFoundError: If template doesn't exist
            TemplateError: If rendering fails
        """
        # Sanitize filename
        safe_name = os.path.basename(name)
        
        try:
            # Load template using Jinja2
            template = self.jinja_env.get_template(safe_name)
            
            # Render with variables
            rendered = template.render(**variables)
            
            logger.info(f"Rendered template: {safe_name}")
            return rendered
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Template '{name}' not found")
        except UndefinedError as e:
            raise TemplateError(f"Missing required variable: {e}")
        except TemplateError as e:
            raise TemplateError(f"Template rendering error: {e}")
        except Exception as e:
            logger.error(f"Error rendering template {safe_name}: {e}")
            raise TemplateError(f"Error rendering template: {e}")
    
    def validate_template(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate ZPL syntax and Jinja2 syntax
        
        Args:
            content: Template content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate ZPL structure
        is_valid, error_msg = validate_zpl_content(content)
        if not is_valid:
            return False, error_msg
        
        # Validate Jinja2 syntax
        try:
            # Try to parse as Jinja2 template
            self.jinja_env.parse(content)
            return True, None
            
        except TemplateError as e:
            return False, f"Jinja2 syntax error: {e}"
        except Exception as e:
            return False, f"Template validation error: {e}"
    
    def extract_variables(self, content: str) -> List[str]:
        """
        Extract variable names from Jinja2 template
        
        Args:
            content: Template content
            
        Returns:
            List of variable names used in template
        """
        try:
            # Parse template to extract variables
            ast = self.jinja_env.parse(content)
            variables = meta.find_undeclared_variables(ast)
            
            # Return sorted list of variables
            return sorted(list(variables))
            
        except Exception as e:
            logger.error(f"Error extracting variables: {e}")
            return []
    
    def parse_metadata(self, content: str) -> Dict[str, Any]:
        """
        Parse metadata from template header comments
        
        Metadata format:
        ^FX Template Metadata
        ^FX name: Shipping Label
        ^FX description: Standard shipping label
        ^FX size: 4x6
        ^FX size_unit: inches (optional, new field)
        ^FX size_width: 4 (optional, new field)
        ^FX size_height: 6 (optional, new field)
        ^FX variables: order_number, customer_name, address
        ^FX created: 2024-01-15
        ^FX modified: 2024-01-20
        
        Args:
            content: Template content
            
        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata = {}
        
        # Extract metadata from ^FX comments
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for ^FX metadata lines
            if line.startswith('^FX') and ':' in line:
                # Remove ^FX prefix
                line = line[3:].strip()
                
                # Skip "Template Metadata" header
                if line.lower() == 'template metadata':
                    continue
                
                # Parse key: value
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # Handle special cases
                    if key == 'variables':
                        # Parse comma-separated list
                        metadata[key] = [v.strip() for v in value.split(',') if v.strip()]
                    elif key in ['size_width', 'size_height']:
                        # Parse numeric values
                        try:
                            metadata[key] = float(value)
                        except ValueError:
                            metadata[key] = value
                    else:
                        metadata[key] = value
        
        # If no unit specified but size exists, default to inches for backward compatibility
        if 'size' in metadata and 'size_unit' not in metadata:
            metadata['size_unit'] = 'inches'
        
        return metadata
    
    def _build_template_with_metadata(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Build template content with metadata header
        
        Args:
            content: ZPL template content
            metadata: Metadata dictionary
            
        Returns:
            Template content with metadata header
        """
        # Remove existing metadata if present
        content_lines = content.split('\n')
        filtered_lines = []
        in_metadata = False
        
        for line in content_lines:
            stripped = line.strip()
            
            # Skip ^XA at start (we'll add it back)
            if stripped == '^XA' and not filtered_lines:
                continue
            
            # Detect metadata section
            if stripped.startswith('^FX') and 'metadata' in stripped.lower():
                in_metadata = True
                continue
            
            # Skip metadata lines
            if in_metadata and stripped.startswith('^FX'):
                continue
            
            # End of metadata section
            if in_metadata and not stripped.startswith('^FX'):
                in_metadata = False
            
            filtered_lines.append(line)
        
        # Build metadata header
        header_lines = ['^XA', '^FX Template Metadata']
        
        # Add metadata fields
        if 'name' in metadata:
            header_lines.append(f"^FX name: {metadata['name']}")
        if 'description' in metadata:
            header_lines.append(f"^FX description: {metadata['description']}")
        if 'size' in metadata:
            header_lines.append(f"^FX size: {metadata['size']}")
            
            # Try to parse and add unit-aware fields
            try:
                label_size = LabelSize.from_string(metadata['size'])
                header_lines.append(f"^FX size_unit: {label_size.unit.value}")
                header_lines.append(f"^FX size_width: {label_size.width}")
                header_lines.append(f"^FX size_height: {label_size.height}")
            except (ValueError, Exception):
                # If parsing fails, just use the legacy format
                pass
        
        if 'variables' in metadata:
            if isinstance(metadata['variables'], list):
                vars_str = ', '.join(metadata['variables'])
            else:
                vars_str = metadata['variables']
            header_lines.append(f"^FX variables: {vars_str}")
        if 'created' in metadata:
            header_lines.append(f"^FX created: {metadata['created']}")
        if 'modified' in metadata:
            header_lines.append(f"^FX modified: {metadata['modified']}")
        
        header_lines.append('')  # Empty line after metadata
        
        # Combine header with content
        return '\n'.join(header_lines + filtered_lines)