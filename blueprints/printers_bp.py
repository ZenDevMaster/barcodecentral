"""
Printers Blueprint for Barcode Central
Handles all printer-related API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
import logging
from printer_manager import PrinterManager
from print_job import create_print_job, execute_print_job

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
printers_bp = Blueprint('printers', __name__)

# Initialize printer manager
printer_manager = PrinterManager()


@printers_bp.route('', methods=['GET'])
@login_required
def list_printers():
    """
    GET /api/printers
    List all configured printers
    """
    try:
        printers = printer_manager.list_printers()
        
        # Optionally check status for each printer
        check_status = request.args.get('check_status', 'false').lower() == 'true'
        
        if check_status:
            for printer in printers:
                printer_id = printer.get('id')
                success, message = printer_manager.test_printer_connection(printer_id, timeout=2)
                printer['status'] = 'online' if success else 'offline'
                printer['last_checked'] = None  # Could add timestamp if needed
        
        return jsonify({
            'success': True,
            'data': {
                'printers': printers,
                'count': len(printers)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing printers: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to list printers',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('/<printer_id>', methods=['GET'])
@login_required
def get_printer(printer_id):
    """
    GET /api/printers/<printer_id>
    Get specific printer details
    """
    try:
        printer = printer_manager.get_printer(printer_id)
        
        if not printer:
            return jsonify({
                'success': False,
                'error': f"Printer '{printer_id}' not found"
            }), 404
        
        return jsonify({
            'success': True,
            'data': printer
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting printer {printer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get printer',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('', methods=['POST'])
@login_required
def add_printer():
    """
    POST /api/printers
    Add a new printer
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Add printer
        success, message = printer_manager.add_printer(data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'printer_id': data.get('id'),
                'name': data.get('name')
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding printer: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to add printer',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('/<printer_id>', methods=['PUT'])
@login_required
def update_printer(printer_id):
    """
    PUT /api/printers/<printer_id>
    Update existing printer
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update printer
        success, message = printer_manager.update_printer(printer_id, data)
        
        if not success:
            status_code = 404 if 'not found' in message.lower() else 400
            return jsonify({
                'success': False,
                'error': message
            }), status_code
        
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'printer_id': printer_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating printer {printer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update printer',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('/<printer_id>', methods=['DELETE'])
@login_required
def delete_printer(printer_id):
    """
    DELETE /api/printers/<printer_id>
    Delete a printer
    """
    try:
        success, message = printer_manager.delete_printer(printer_id)
        
        if not success:
            status_code = 404 if 'not found' in message.lower() else 400
            return jsonify({
                'success': False,
                'error': message
            }), status_code
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting printer {printer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete printer',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('/<printer_id>/test', methods=['POST'])
@login_required
def test_printer(printer_id):
    """
    POST /api/printers/<printer_id>/test
    Test printer connection
    """
    try:
        # Get timeout from request body if provided
        data = request.get_json() or {}
        timeout = data.get('timeout', 5)
        
        # Test connection
        success, message = printer_manager.test_printer_connection(printer_id, timeout=timeout)
        
        if not success:
            # Determine appropriate status code
            if 'not found' in message.lower():
                status_code = 404
            elif 'timed out' in message.lower():
                status_code = 504
            elif 'failed to connect' in message.lower():
                status_code = 503
            else:
                status_code = 500
            
            return jsonify({
                'success': False,
                'error': message
            }), status_code
        
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'printer_id': printer_id,
                'status': 'online'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing printer {printer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to test printer',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('/<printer_id>/validate', methods=['POST'])
@login_required
def validate_printer(printer_id):
    """
    POST /api/printers/<printer_id>/validate
    Validate printer compatibility with label size
    """
    try:
        data = request.get_json()
        
        if not data or 'label_size' not in data:
            return jsonify({
                'success': False,
                'error': 'label_size is required'
            }), 400
        
        label_size = data['label_size']
        
        # Test connection
        reachable, conn_msg = printer_manager.test_printer_connection(printer_id, timeout=5)
        
        # Check compatibility
        compatible, compat_msg = printer_manager.validate_printer_compatibility(printer_id, label_size)
        
        warnings = []
        if not compatible:
            warnings.append(compat_msg)
        
        if not reachable:
            return jsonify({
                'success': False,
                'error': 'Printer unreachable',
                'details': {
                    'message': conn_msg
                }
            }), 503
        
        return jsonify({
            'success': True,
            'data': {
                'reachable': reachable,
                'compatible': compatible,
                'warnings': warnings
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating printer {printer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate printer',
            'details': {'message': str(e)}
        }), 500


@printers_bp.route('/<printer_id>/print', methods=['POST'])
@login_required
def print_label(printer_id):
    """
    POST /api/printers/<printer_id>/print
    Send ZPL to printer (direct ZPL or via template)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Check if direct ZPL or template-based
        if 'zpl' in data:
            # Direct ZPL printing
            zpl_content = data['zpl']
            quantity = data.get('quantity', 1)
            
            success, message = printer_manager.send_zpl(printer_id, zpl_content, quantity)
            
            if not success:
                # Determine appropriate status code
                if 'not found' in message.lower():
                    status_code = 404
                elif 'disabled' in message.lower():
                    status_code = 400
                elif 'timed out' in message.lower():
                    status_code = 504
                elif 'failed to connect' in message.lower():
                    status_code = 503
                else:
                    status_code = 500
                
                return jsonify({
                    'success': False,
                    'error': message
                }), status_code
            
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'printer_id': printer_id,
                    'quantity': quantity
                }
            }), 200
            
        elif 'template' in data:
            # Template-based printing
            template_name = data['template']
            variables = data.get('variables', {})
            quantity = data.get('quantity', 1)
            
            # Create and execute print job
            job = create_print_job(template_name, printer_id, variables, quantity)
            success, message, job_dict = execute_print_job(job)
            
            if not success:
                # Determine appropriate status code based on error
                if 'not found' in message.lower():
                    status_code = 404
                elif 'disabled' in message.lower() or 'missing required' in message.lower():
                    status_code = 400
                elif 'timed out' in message.lower():
                    status_code = 504
                elif 'failed to connect' in message.lower():
                    status_code = 503
                else:
                    status_code = 500
                
                return jsonify({
                    'success': False,
                    'error': message,
                    'details': job_dict
                }), status_code
            
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'printer_id': printer_id,
                    'template': template_name,
                    'quantity': quantity,
                    'timestamp': job_dict.get('timestamp')
                }
            }), 200
        
        else:
            return jsonify({
                'success': False,
                'error': 'Either "zpl" or "template" must be provided'
            }), 400
        
    except Exception as e:
        logger.error(f"Error printing to {printer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to print',
            'details': {'message': str(e)}
        }), 500