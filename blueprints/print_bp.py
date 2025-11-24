"""
Print Blueprint for Barcode Central
Handles complete print workflow: validation, rendering, preview, and printing
"""
import logging
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from template_manager import TemplateManager
from printer_manager import PrinterManager
from preview_generator import PreviewGenerator
from print_job import PrintJob

logger = logging.getLogger(__name__)

# Create blueprint
print_bp = Blueprint('print', __name__)

# Initialize managers
template_manager = TemplateManager()
printer_manager = PrinterManager()
preview_generator = PreviewGenerator()


@print_bp.route('/', methods=['POST'])
@login_required
def print_label():
    """
    Complete print workflow: render, preview, and print
    
    Request JSON:
    {
        "template": "example.zpl.j2",
        "printer_id": "zebra-warehouse-01",
        "variables": {
            "order_number": "12345",
            "customer_name": "John Doe"
        },
        "quantity": 1,
        "generate_preview": true,
        "label_size": "4x6",  // Optional, extracted from template if not provided
        "dpi": 203  // Optional, extracted from printer if not provided
    }
    
    Response:
    {
        "success": true,
        "message": "Print job completed successfully",
        "job_id": "uuid",
        "preview_url": "/api/preview/abc123.png",
        "printer": "Zebra ZT230 - Warehouse",
        "quantity": 1,
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Extract parameters
        template_name = data.get('template')
        printer_id = data.get('printer_id')
        variables = data.get('variables', {})
        quantity = data.get('quantity', 1)
        generate_preview = data.get('generate_preview', True)
        
        # Validate required fields
        if not template_name:
            return jsonify({
                'success': False,
                'error': 'Template name is required'
            }), 400
        
        if not printer_id:
            return jsonify({
                'success': False,
                'error': 'Printer ID is required'
            }), 400
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            return jsonify({
                'success': False,
                'error': 'Quantity must be between 1 and 100'
            }), 400
        
        # Get current user
        username = current_user.username if current_user.is_authenticated else 'unknown'
        
        # Step 1: Validate template exists
        try:
            template = template_manager.get_template(template_name)
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': f"Template '{template_name}' not found"
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"Error loading template: {str(e)}"
            }), 500
        
        # Step 2: Validate printer exists
        printer = printer_manager.get_printer(printer_id)
        if not printer:
            return jsonify({
                'success': False,
                'error': f"Printer '{printer_id}' not found"
            }), 404
        
        if not printer.get('enabled', True):
            return jsonify({
                'success': False,
                'error': f"Printer '{printer_id}' is disabled"
            }), 400
        
        # Step 3: Validate printer compatibility
        label_size = data.get('label_size') or template.get('size', '4x6')
        is_compatible, compat_msg = printer_manager.validate_printer_compatibility(
            printer_id, label_size
        )
        if not is_compatible:
            return jsonify({
                'success': False,
                'error': compat_msg
            }), 400
        
        # Step 4: Render template
        try:
            rendered_zpl = template_manager.render_template(template_name, variables)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"Error rendering template: {str(e)}"
            }), 400
        
        # Step 5: Generate preview (if requested)
        preview_url = None
        preview_filename = None
        
        if generate_preview:
            try:
                dpi = data.get('dpi') or printer.get('dpi', 203)
                
                success, filename, error_msg = preview_generator.save_preview(
                    rendered_zpl,
                    filename=None,
                    label_size=label_size,
                    dpi=dpi,
                    format='png'
                )
                
                if success:
                    preview_url = f"/api/preview/{filename}"
                    preview_filename = filename
                    logger.info(f"Generated preview: {filename}")
                else:
                    # Log warning but don't fail the print job
                    logger.warning(f"Failed to generate preview: {error_msg}")
                    
            except Exception as e:
                # Log error but don't fail the print job
                logger.error(f"Error generating preview: {str(e)}")
        
        # Step 6: Create and execute print job (with history logging)
        job = PrintJob(
            template_name=template_name,
            printer_id=printer_id,
            variables=variables,
            quantity=quantity,
            generate_preview=False,  # Already generated above
            log_to_history=True,
            user=username
        )
        
        # Set the rendered ZPL and preview info
        job.rendered_zpl = rendered_zpl
        job.preview_filename = preview_filename
        job.preview_url = preview_url
        
        # Send to printer
        send_success, send_msg = printer_manager.send_zpl(
            printer_id,
            rendered_zpl,
            quantity
        )
        
        if not send_success:
            job.status = 'failed'
            job.error_message = send_msg
            
            # Log failed print to history
            job._log_to_history()
            
            return jsonify({
                'success': False,
                'error': send_msg,
                'job_id': job.job_id,
                'preview_url': preview_url
            }), 500
        
        # Success - update job status and log to history
        job.status = 'success'
        job._log_to_history()
        
        # Success response
        response_data = {
            'success': True,
            'message': f"Successfully printed {quantity} label(s)",
            'job_id': job.job_id,
            'printer': printer.get('name', printer_id),
            'printer_id': printer_id,
            'template': template_name,
            'quantity': quantity,
            'timestamp': job.timestamp
        }
        
        # Add preview URL if generated
        if preview_url:
            response_data['preview_url'] = preview_url
            response_data['preview_filename'] = preview_filename
        
        logger.info(f"Print job {job.job_id} completed successfully: {template_name} -> {printer_id} (x{quantity})")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in print_label: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@print_bp.route('/preview-only', methods=['POST'])
@login_required
def preview_only():
    """
    Render and preview without printing
    
    Request JSON:
    {
        "template": "example.zpl.j2",
        "variables": {
            "order_number": "12345"
        },
        "label_size": "4x6",
        "dpi": 203
    }
    
    Response:
    {
        "success": true,
        "preview_url": "/api/preview/abc123.png",
        "filename": "abc123.png",
        "zpl": "^XA..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Extract parameters
        template_name = data.get('template')
        variables = data.get('variables', {})
        label_size = data.get('label_size', '4x6')
        dpi = data.get('dpi', 203)
        
        # Validate required fields
        if not template_name:
            return jsonify({
                'success': False,
                'error': 'Template name is required'
            }), 400
        
        # Step 1: Validate template exists
        try:
            template = template_manager.get_template(template_name)
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': f"Template '{template_name}' not found"
            }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"Error loading template: {str(e)}"
            }), 500
        
        # Use template's label size if not provided
        if not label_size and 'size' in template:
            label_size = template['size']
        
        # Step 2: Render template
        try:
            rendered_zpl = template_manager.render_template(template_name, variables)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"Error rendering template: {str(e)}"
            }), 400
        
        # Step 3: Generate preview
        success, filename, error_msg = preview_generator.save_preview(
            rendered_zpl,
            filename=None,
            label_size=label_size,
            dpi=dpi,
            format='png'
        )
        
        if not success:
            # Check if it's a Labelary API error
            if 'Labelary' in error_msg or 'connect' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'offline': True,
                    'zpl': rendered_zpl
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'zpl': rendered_zpl
                }), 500
        
        # Success response
        preview_url = f"/api/preview/{filename}"
        
        logger.info(f"Generated preview-only: {filename}")
        
        return jsonify({
            'success': True,
            'preview_url': preview_url,
            'filename': filename,
            'zpl': rendered_zpl,
            'label_size': label_size,
            'dpi': dpi
        }), 200
        
    except Exception as e:
        logger.error(f"Error in preview_only: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@print_bp.route('/status/<job_id>', methods=['GET'])
@login_required
def get_job_status(job_id):
    """
    Get print job status (placeholder for future async support)
    
    Args:
        job_id: Job ID to query
        
    Response:
    {
        "success": true,
        "job_id": "uuid",
        "status": "completed",
        "message": "Job completed successfully"
    }
    """
    try:
        # For now, this is a placeholder
        # In future phases, this could query a job queue or database
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'unknown',
            'message': 'Job status tracking not yet implemented'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_job_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@print_bp.route('/validate', methods=['POST'])
@login_required
def validate_print_job():
    """
    Validate print job without executing
    
    Request JSON:
    {
        "template": "example.zpl.j2",
        "printer_id": "zebra-warehouse-01",
        "variables": {
            "order_number": "12345"
        },
        "quantity": 1
    }
    
    Response:
    {
        "success": true,
        "valid": true,
        "message": "Print job is valid",
        "template": {...},
        "printer": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Extract parameters
        template_name = data.get('template')
        printer_id = data.get('printer_id')
        variables = data.get('variables', {})
        quantity = data.get('quantity', 1)
        
        # Validate required fields
        if not template_name:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Template name is required'
            }), 200
        
        if not printer_id:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Printer ID is required'
            }), 200
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Quantity must be between 1 and 100'
            }), 200
        
        # Create print job and validate
        job = PrintJob(template_name, printer_id, variables, quantity)
        is_valid, validation_msg = job.validate()
        
        if not is_valid:
            return jsonify({
                'success': True,
                'valid': False,
                'error': validation_msg
            }), 200
        
        # Get template and printer details
        template = template_manager.get_template(template_name)
        printer = printer_manager.get_printer(printer_id)
        
        return jsonify({
            'success': True,
            'valid': True,
            'message': 'Print job is valid',
            'template': {
                'name': template.get('name'),
                'filename': template_name,
                'size': template.get('size')
            },
            'printer': {
                'id': printer_id,
                'name': printer.get('name'),
                'ip': printer.get('ip')
            },
            'quantity': quantity
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_print_job: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500