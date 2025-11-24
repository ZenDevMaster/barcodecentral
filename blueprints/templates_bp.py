"""
Templates Blueprint for Barcode Central
Handles template CRUD operations, rendering, and validation
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required
from jinja2 import TemplateError

from template_manager import TemplateManager

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
        
        # Extract required fields
        filename = data.get('filename')
        content = data.get('content')
        
        if not filename:
            return error_response("Field 'filename' is required", 400)
        if not content:
            return error_response("Field 'content' is required", 400)
        
        # Build metadata
        metadata = {
            'name': data.get('name', filename),
            'description': data.get('description', ''),
            'size': data.get('label_size', data.get('size', '')),
            'created': data.get('created', ''),
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
        
        # Extract content
        content = data.get('content')
        if not content:
            return error_response("Field 'content' is required", 400)
        
        # Build metadata
        metadata = {
            'name': data.get('name', filename),
            'description': data.get('description', ''),
            'size': data.get('label_size', data.get('size', '')),
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