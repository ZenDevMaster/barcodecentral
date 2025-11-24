"""
Templates Blueprint for Barcode Central
Handles template CRUD operations, rendering, and validation
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required
from jinja2 import TemplateError

from template_manager import TemplateManager
from utils import generate_template_filename

logger = logging.getLogger(__name__)

# Create blueprint
templates_bp = Blueprint('templates', __name__)

# Initialize template manager
template_manager = TemplateManager()


def success_response(data=None, message=None):
    """
    Create a success response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        JSON response with success=True
    """
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return jsonify(response)


def error_response(error, status_code=400, details=None):
    """
    Create an error response
    
    Args:
        error: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        JSON response with success=False
    """
    response = {
        'success': False,
        'error': error
    }
    if details:
        response['details'] = details
    return jsonify(response), status_code


@templates_bp.route('', methods=['GET'])
@login_required
def list_templates():
    """
    GET /api/templates
    List all available ZPL templates
    
    Query Parameters:
        include_content (optional): Include template content in response
        
    Returns:
        JSON response with list of templates
    """
    try:
        include_content = request.args.get('include_content', 'false').lower() == 'true'
        
        templates = template_manager.list_templates()
        
        # Remove content if not requested
        if not include_content:
            for template in templates:
                template.pop('content', None)
        
        return success_response({
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return error_response(f"Error listing templates: {e}", 500)


@templates_bp.route('/<filename>', methods=['GET'])
@login_required
def get_template(filename):
    """
    GET /api/templates/<filename>
    Get specific template details and content
    
    Path Parameters:
        filename: Template filename
        
    Returns:
        JSON response with template details
    """
    try:
        template = template_manager.get_template(filename)
        return success_response(template)
        
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except Exception as e:
        logger.error(f"Error getting template {filename}: {e}")
        return error_response(f"Error getting template: {e}", 500)


@templates_bp.route('', methods=['POST'])
@login_required
def create_template():
    """
    POST /api/templates
    Create a new ZPL template
    
    Request Body:
        {
            "filename": "new_label.zpl.j2",
            "name": "New Label",
            "description": "Custom label template",
            "label_size": "4x6",
            "content": "^XA...^XZ"
        }
        
    Returns:
        JSON response with created template info
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        # Extract required fields - support both old and new formats
        # Old format: filename + content
        # New format: name (display name) + zpl_content + label_width + label_height
        display_name = data.get('name')
        content = data.get('content') or data.get('zpl_content')
        
        # Generate filename from display name if not explicitly provided
        if data.get('filename'):
            # Explicit filename provided (legacy support)
            filename = data.get('filename')
        elif display_name:
            # Generate filename from display name
            filename = generate_template_filename(display_name)
        else:
            return error_response("Field 'name' (display name) is required", 400)
        
        if not content:
            return error_response("Field 'content' or 'zpl_content' is required", 400)
        
        # Build label size from separate width/height or combined size string
        label_size = ''
        if data.get('label_width') and data.get('label_height'):
            # Support unit suffixes (e.g., "50mm", "15mm", "2cm", "4")
            width_str = str(data.get('label_width')).strip()
            height_str = str(data.get('label_height')).strip()
            
            logger.debug(f"Parsing label size: width='{width_str}', height='{height_str}'")
            
            # Parse and convert units if needed
            from utils.unit_converter import mm_to_inches
            
            # Helper function to parse individual dimension with unit
            def parse_dimension(dim_str):
                """Parse a dimension string like '50mm', '2cm', or '4' and return value in inches"""
                dim_str = dim_str.strip().lower()
                
                if dim_str.endswith('mm'):
                    # Millimeters
                    value = float(dim_str[:-2].strip())
                    return mm_to_inches(value)
                elif dim_str.endswith('cm'):
                    # Centimeters -> convert to mm first
                    value = float(dim_str[:-2].strip())
                    return mm_to_inches(value * 10)
                elif dim_str.endswith('in') or dim_str.endswith('inches'):
                    # Inches (explicit)
                    if dim_str.endswith('inches'):
                        value = float(dim_str[:-6].strip())
                    else:
                        value = float(dim_str[:-2].strip())
                    return value
                else:
                    # No unit - assume inches
                    return float(dim_str)
            
            # Parse with unit support
            try:
                width_inches = parse_dimension(width_str)
                height_inches = parse_dimension(height_str)
                
                label_size = f"{width_inches:.1f}x{height_inches:.1f}"
                logger.debug(f"Successfully parsed label size: '{label_size}' inches")
            except (ValueError, AttributeError) as e:
                logger.error(f"Failed to parse label dimensions: {e}")
                return error_response(f"Invalid label dimensions: '{width_str}' x '{height_str}'. Use format like '50mm', '2cm', or '4'", 400)
        elif data.get('label_size') or data.get('size'):
            label_size = data.get('label_size', data.get('size', ''))
        
        # Validate that we have a label size
        if not label_size:
            return error_response("Label size is required. Please provide width and height.", 400)
        
        # Build metadata - use display_name for the metadata 'name' field
        metadata = {
            'name': display_name or filename.replace('.zpl.j2', '').replace('_', ' ').title(),
            'description': data.get('description', ''),
            'size': label_size,
            'created': data.get('created', ''),
            'variables': data.get('variables', [])
        }
        
        # Create template
        filepath = template_manager.create_template(filename, content, metadata)
        
        return success_response(
            {
                'filename': filename,
                'path': filepath
            },
            "Template created successfully"
        ), 201
        
    except FileExistsError as e:
        return error_response(str(e), 409)
    except ValueError as e:
        return error_response(str(e), 422)
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return error_response(f"Error creating template: {e}", 500)


@templates_bp.route('/<filename>', methods=['PUT'])
@login_required
def update_template(filename):
    """
    PUT /api/templates/<filename>
    Update existing template
    
    Path Parameters:
        filename: Template filename
        
    Request Body:
        {
            "name": "Updated Label Name",
            "description": "Updated description",
            "label_size": "4x6",
            "content": "^XA...^XZ"
        }
        
    Returns:
        JSON response with updated template info
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        # Log incoming request for debugging
        logger.info(f"[UPDATE_TEMPLATE] Received data keys: {list(data.keys())}")
        logger.info(f"[UPDATE_TEMPLATE] Has 'content': {bool(data.get('content'))}, Has 'zpl_content': {bool(data.get('zpl_content'))}")
        
        # Extract content - support both 'content' and 'zpl_content' field names
        content = data.get('content') or data.get('zpl_content')
        if not content:
            return error_response("Field 'content' or 'zpl_content' is required", 400)
        
        # Build label size from separate width/height or combined size string
        label_size = ''
        if data.get('label_width') and data.get('label_height'):
            # Support unit suffixes (e.g., "2.3mm", "1.2cm")
            width_str = str(data.get('label_width')).strip()
            height_str = str(data.get('label_height')).strip()
            
            # Parse and convert units if needed
            from utils.label_size import LabelSize
            from utils.unit_converter import parse_size_string, mm_to_inches
            
            # Check if width has unit suffix
            width_val = width_str
            height_val = height_str
            
            # Convert cm to mm for parsing
            if width_str.lower().endswith('cm'):
                width_val = str(float(width_str[:-2].strip()) * 10) + 'mm'
            if height_str.lower().endswith('cm'):
                height_val = str(float(height_str[:-2].strip()) * 10) + 'mm'
            
            # Parse with unit support
            try:
                # Try parsing as size string with units
                temp_size = f"{width_val}x{height_val}"
                width, height, unit = parse_size_string(temp_size)
                
                # Convert to inches for storage (standard format)
                if unit.value == 'mm':
                    width = mm_to_inches(width)
                    height = mm_to_inches(height)
                
                label_size = f"{width:.1f}x{height:.1f}"
            except (ValueError, AttributeError):
                # Fall back to treating as plain numbers (inches)
                try:
                    width = float(width_str.rstrip('inchesIN '))
                    height = float(height_str.rstrip('inchesIN '))
                    label_size = f"{width:.1f}x{height:.1f}"
                except ValueError:
                    pass
        elif data.get('label_size') or data.get('size'):
            label_size = data.get('label_size', data.get('size', ''))
        
        # Build metadata
        metadata = {
            'name': data.get('name', filename),
            'description': data.get('description', ''),
            'size': label_size,
        }
        
        # Update template
        filepath = template_manager.update_template(filename, content, metadata)
        
        # Get updated template info
        template = template_manager.get_template(filename)
        
        return success_response(
            {
                'filename': filename,
                'modified': template.get('modified')
            },
            "Template updated successfully"
        )
        
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except ValueError as e:
        return error_response(str(e), 422)
    except Exception as e:
        logger.error(f"Error updating template {filename}: {e}")
        return error_response(f"Error updating template: {e}", 500)


@templates_bp.route('/<filename>', methods=['DELETE'])
@login_required
def delete_template(filename):
    """
    DELETE /api/templates/<filename>
    Delete a template
    
    Path Parameters:
        filename: Template filename
        
    Returns:
        JSON response confirming deletion
    """
    try:
        template_manager.delete_template(filename)
        
        return success_response(
            message="Template deleted successfully"
        )
        
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except Exception as e:
        logger.error(f"Error deleting template {filename}: {e}")
        return error_response(f"Error deleting template: {e}", 500)


@templates_bp.route('/<filename>/render', methods=['POST'])
@login_required
def render_template(filename):
    """
    POST /api/templates/<filename>/render
    Render template with variables to generate ZPL code
    
    Path Parameters:
        filename: Template filename
        
    Request Body:
        {
            "variables": {
                "name": "John Doe",
                "address": "123 Main St",
                ...
            }
        }
        
    Returns:
        JSON response with rendered ZPL code
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        variables = data.get('variables', {})
        
        if not isinstance(variables, dict):
            return error_response("Field 'variables' must be a dictionary", 400)
        
        # Render template
        rendered_zpl = template_manager.render_template(filename, variables)
        
        # Get template info to extract variable list
        template = template_manager.get_template(filename)
        
        return success_response({
            'zpl': rendered_zpl,
            'variables_used': template.get('variables', [])
        })
        
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except TemplateError as e:
        # Extract missing variable info if possible
        error_msg = str(e)
        details = {}
        
        # Try to parse missing variable from error message
        if 'undefined' in error_msg.lower():
            details['type'] = 'missing_variable'
        
        return error_response(error_msg, 400, details)
    except Exception as e:
        logger.error(f"Error rendering template {filename}: {e}")
        return error_response(f"Error rendering template: {e}", 500)


@templates_bp.route('/<filename>/validate', methods=['POST'])
@login_required
def validate_template(filename):
    """
    POST /api/templates/<filename>/validate
    Validate template syntax
    
    Path Parameters:
        filename: Template filename
        
    Returns:
        JSON response with validation result
    """
    try:
        # Get template content
        template = template_manager.get_template(filename)
        content = template.get('content', '')
        
        # Validate template
        is_valid, error_msg = template_manager.validate_template(content)
        
        if is_valid:
            return success_response({
                'valid': True,
                'message': 'Template is valid'
            })
        else:
            return success_response({
                'valid': False,
                'error': error_msg
            })
        
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except Exception as e:
        logger.error(f"Error validating template {filename}: {e}")
        return error_response(f"Error validating template: {e}", 500)


@templates_bp.route('/<filename>/variables', methods=['GET'])
@login_required
def get_template_variables(filename):
    """
    GET /api/templates/<filename>/variables
    Extract variables from template
    
    Path Parameters:
        filename: Template filename
        
    Returns:
        JSON response with list of variables
    """
    try:
        # Get template content
        template = template_manager.get_template(filename)
        
        return success_response({
            'variables': template.get('variables', []),
            'count': len(template.get('variables', []))
        })
        
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except Exception as e:
        logger.error(f"Error extracting variables from template {filename}: {e}")
        return error_response(f"Error extracting variables: {e}", 500)