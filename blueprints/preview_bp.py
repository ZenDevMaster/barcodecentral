"""
Preview Blueprint for Barcode Central
Handles preview generation, retrieval, and management endpoints
"""
import os
import logging
from flask import Blueprint, request, jsonify, send_file
from preview_generator import PreviewGenerator
from template_manager import TemplateManager
from utils.preview_utils import generate_preview_filename, validate_label_size

logger = logging.getLogger(__name__)

# Create blueprint
preview_bp = Blueprint('preview', __name__)

# Initialize managers
preview_generator = PreviewGenerator()
template_manager = TemplateManager()


@preview_bp.route('/generate', methods=['POST'])
def generate_preview():
    """
    Generate preview from ZPL or template
    
    Request JSON:
    {
        "zpl": "^XA^FO50,50^FDTest^FS^XZ",  // OR
        "template": "example.zpl.j2",
        "variables": {"order_number": "12345"},
        "label_size": "4x6",
        "dpi": 203,
        "format": "png"
    }
    
    Response:
    {
        "success": true,
        "preview_url": "/api/preview/abc123.png",
        "filename": "abc123.png"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Get ZPL content (either directly or from template)
        zpl_content = None
        
        if 'zpl' in data:
            # Direct ZPL provided
            zpl_content = data['zpl']
            
        elif 'template' in data:
            # Render template with variables
            template_name = data['template']
            variables = data.get('variables', {})
            
            try:
                zpl_content = template_manager.render_template(template_name, variables)
            except FileNotFoundError:
                return jsonify({
                    'success': False,
                    'error': f"Template '{template_name}' not found"
                }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f"Error rendering template: {str(e)}"
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Either "zpl" or "template" must be provided'
            }), 400
        
        # Validate ZPL content
        if not zpl_content or not isinstance(zpl_content, str):
            return jsonify({
                'success': False,
                'error': 'ZPL content cannot be empty'
            }), 400
        
        # Get parameters
        label_size = data.get('label_size', '4x6')
        dpi = data.get('dpi', 203)
        format = data.get('format', 'png')
        
        # Validate label size
        is_valid, error_msg = validate_label_size(label_size)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Validate format
        if format not in ['png', 'pdf']:
            return jsonify({
                'success': False,
                'error': f"Invalid format '{format}'. Must be 'png' or 'pdf'"
            }), 400
        
        # Generate and save preview
        success, filename, error_msg = preview_generator.save_preview(
            zpl_content,
            filename=None,  # Auto-generate UUID filename
            label_size=label_size,
            dpi=dpi,
            format=format
        )
        
        if not success:
            # Check if it's a Labelary API error
            if 'Labelary' in error_msg or 'connect' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'offline': True
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 500
        
        # Return success with preview URL
        preview_url = f"/api/preview/{filename}"
        
        logger.info(f"Generated preview: {filename}")
        
        return jsonify({
            'success': True,
            'preview_url': preview_url,
            'filename': filename,
            'label_size': label_size,
            'dpi': dpi,
            'format': format
        }), 200
        
    except Exception as e:
        logger.error(f"Error in generate_preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@preview_bp.route('/<filename>', methods=['GET'])
def get_preview(filename):
    """
    Serve preview image file
    
    Args:
        filename: Preview filename (e.g., 'abc123.png')
        
    Response:
        Image file (PNG or PDF)
    """
    try:
        # Sanitize filename (prevent directory traversal)
        safe_filename = os.path.basename(filename)
        
        # Check if preview exists
        if not preview_generator.preview_exists(safe_filename):
            return jsonify({
                'success': False,
                'error': f"Preview '{safe_filename}' not found"
            }), 404
        
        # Get full path
        filepath = preview_generator.get_preview_path(safe_filename)
        
        # Determine mimetype
        if safe_filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        elif safe_filename.endswith('.png'):
            mimetype = 'image/png'
        else:
            mimetype = 'application/octet-stream'
        
        # Send file
        return send_file(
            filepath,
            mimetype=mimetype,
            as_attachment=False,
            download_name=safe_filename
        )
        
    except Exception as e:
        logger.error(f"Error serving preview {filename}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error serving preview: {str(e)}"
        }), 500


@preview_bp.route('/pdf', methods=['POST'])
def generate_pdf():
    """
    Generate PDF preview from ZPL or template
    
    Request JSON:
    {
        "zpl": "^XA^FO50,50^FDTest^FS^XZ",  // OR
        "template": "example.zpl.j2",
        "variables": {"order_number": "12345"},
        "label_size": "4x6",
        "dpi": 203
    }
    
    Response:
    {
        "success": true,
        "preview_url": "/api/preview/abc123.pdf",
        "filename": "abc123.pdf"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Force format to PDF
        data['format'] = 'pdf'
        
        # Use the generate_preview endpoint logic
        request._cached_json = (data, data)
        return generate_preview()
        
    except Exception as e:
        logger.error(f"Error in generate_pdf: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@preview_bp.route('/<filename>', methods=['DELETE'])
def delete_preview(filename):
    """
    Delete a preview file
    
    Args:
        filename: Preview filename to delete
        
    Response:
    {
        "success": true,
        "message": "Preview deleted successfully"
    }
    """
    try:
        # Sanitize filename
        safe_filename = os.path.basename(filename)
        
        # Check if preview exists
        if not preview_generator.preview_exists(safe_filename):
            return jsonify({
                'success': False,
                'error': f"Preview '{safe_filename}' not found"
            }), 404
        
        # Delete file
        filepath = preview_generator.get_preview_path(safe_filename)
        os.remove(filepath)
        
        logger.info(f"Deleted preview: {safe_filename}")
        
        return jsonify({
            'success': True,
            'message': 'Preview deleted successfully',
            'filename': safe_filename
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting preview {filename}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error deleting preview: {str(e)}"
        }), 500


@preview_bp.route('/cleanup', methods=['POST'])
def cleanup_previews():
    """
    Cleanup old preview files
    
    Request JSON:
    {
        "days": 7  // Optional, default is 7
    }
    
    Response:
    {
        "success": true,
        "files_deleted": 5,
        "errors": 0,
        "message": "Cleanup completed"
    }
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 7)
        
        # Validate days parameter
        if not isinstance(days, int) or days < 1:
            return jsonify({
                'success': False,
                'error': 'Days must be a positive integer'
            }), 400
        
        # Perform cleanup
        files_deleted, errors = preview_generator.cleanup_old_previews(days)
        
        logger.info(f"Cleanup completed: {files_deleted} files deleted, {errors} errors")
        
        return jsonify({
            'success': True,
            'files_deleted': files_deleted,
            'errors': errors,
            'message': f"Cleanup completed: {files_deleted} files deleted",
            'days': days
        }), 200
        
    except Exception as e:
        logger.error(f"Error in cleanup_previews: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@preview_bp.route('/status', methods=['GET'])
def preview_status():
    """
    Get preview system status
    
    Response:
    {
        "success": true,
        "previews_dir": "previews",
        "total_files": 10,
        "total_size": "2.5 MB"
    }
    """
    try:
        previews_dir = preview_generator.previews_dir
        
        # Count files and calculate total size
        total_files = 0
        total_size = 0
        
        if os.path.exists(previews_dir):
            for filename in os.listdir(previews_dir):
                filepath = os.path.join(previews_dir, filename)
                if os.path.isfile(filepath):
                    total_files += 1
                    total_size += os.path.getsize(filepath)
        
        # Format size
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        
        return jsonify({
            'success': True,
            'previews_dir': previews_dir,
            'total_files': total_files,
            'total_size': size_str,
            'total_size_bytes': total_size
        }), 200
        
    except Exception as e:
        logger.error(f"Error in preview_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500