"""
History Blueprint for Barcode Central
Handles print job history operations: list, view, search, reprint, delete
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from history_manager import HistoryManager
from printer_manager import PrinterManager
from template_manager import TemplateManager
from preview_generator import PreviewGenerator
from utils.statistics import (
    calculate_print_statistics,
    get_top_templates,
    get_top_printers,
    get_print_volume_by_date,
    get_success_rate,
    get_user_statistics,
    get_label_size_distribution,
    get_hourly_distribution,
    get_recent_activity
)

logger = logging.getLogger(__name__)

# Create blueprint
history_bp = Blueprint('history', __name__)

# Initialize managers
history_manager = HistoryManager()
printer_manager = PrinterManager()
template_manager = TemplateManager()
preview_generator = PreviewGenerator()


@history_bp.route('/', methods=['GET'])
@login_required
def list_history():
    """
    Get paginated and filtered history entries
    
    Query Parameters:
    - limit: Number of entries (default: 100, max: 500)
    - offset: Pagination offset (default: 0)
    - template: Filter by template name
    - printer_id: Filter by printer ID
    - status: Filter by status (success/failed)
    - start_date: Filter by start date (ISO 8601)
    - end_date: Filter by end date (ISO 8601)
    
    Response:
    {
        "success": true,
        "data": {
            "entries": [...],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "total": 150
            }
        }
    }
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        template = request.args.get('template')
        printer_id = request.args.get('printer_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Validate parameters
        if limit < 1 or limit > 500:
            return jsonify({
                'success': False,
                'error': 'Limit must be between 1 and 500'
            }), 400
        
        if offset < 0:
            return jsonify({
                'success': False,
                'error': 'Offset must be non-negative'
            }), 400
        
        # Get entries
        entries, total_count = history_manager.get_entries(
            limit=limit,
            offset=offset,
            template=template,
            printer_id=printer_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        # Remove rendered_zpl from list view (too large)
        for entry in entries:
            entry.pop('rendered_zpl', None)
        
        return jsonify({
            'success': True,
            'data': {
                'entries': entries,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total': total_count
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing history: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/<entry_id>', methods=['GET'])
@login_required
def get_history_entry(entry_id):
    """
    Get specific history entry details
    
    Args:
        entry_id: History entry UUID
        
    Response:
    {
        "success": true,
        "data": {
            "id": "uuid",
            "timestamp": "...",
            "template": "...",
            "variables": {...},
            "rendered_zpl": "...",
            ...
        }
    }
    """
    try:
        entry = history_manager.get_entry(entry_id)
        
        if not entry:
            return jsonify({
                'success': False,
                'error': 'History entry not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': entry
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting history entry {entry_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/<entry_id>', methods=['DELETE'])
@login_required
def delete_history_entry(entry_id):
    """
    Delete a history entry
    
    Args:
        entry_id: History entry UUID
        
    Response:
    {
        "success": true,
        "message": "History entry deleted successfully"
    }
    """
    try:
        success, message = history_manager.delete_entry(entry_id)
        
        if not success:
            if 'not found' in message.lower():
                return jsonify({
                    'success': False,
                    'error': message
                }), 404
            else:
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
        
        logger.info(f"User {current_user.username} deleted history entry {entry_id}")
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting history entry {entry_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/<entry_id>/reprint', methods=['POST'])
@login_required
def reprint_from_history(entry_id):
    """
    Reprint a label from history
    
    Args:
        entry_id: History entry UUID
        
    Request JSON:
    {
        "printer_id": "zebra-warehouse-01",  // Optional, uses original if not provided
        "quantity": 3,  // Optional, uses original if not provided
        "variables": {...}  // Optional, uses original if not provided
    }
    
    Response:
    {
        "success": true,
        "message": "Reprint job sent successfully",
        "data": {
            "job_id": "new-uuid",
            "original_job_id": "original-uuid",
            "printer_id": "...",
            "quantity": 3,
            "timestamp": "..."
        }
    }
    """
    try:
        # Get original history entry
        original_entry = history_manager.get_entry(entry_id)
        
        if not original_entry:
            return jsonify({
                'success': False,
                'error': 'History entry not found'
            }), 404
        
        # Get request data
        data = request.get_json() or {}
        
        # Use original values or override with new ones
        printer_id = data.get('printer_id', original_entry.get('printer_id'))
        quantity = data.get('quantity', original_entry.get('quantity', 1))
        variables = data.get('variables', original_entry.get('variables', {}))
        
        # Validate printer exists and is enabled
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
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            return jsonify({
                'success': False,
                'error': 'Quantity must be between 1 and 100'
            }), 400
        
        # Get rendered ZPL from history or re-render if variables changed
        rendered_zpl = original_entry.get('rendered_zpl')
        
        if not rendered_zpl or variables != original_entry.get('variables'):
            # Need to re-render template
            template_name = original_entry.get('template')
            if not template_name:
                return jsonify({
                    'success': False,
                    'error': 'Original template name not found in history'
                }), 400
            
            try:
                rendered_zpl = template_manager.render_template(template_name, variables)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f"Error rendering template: {str(e)}"
                }), 400
        
        # Generate new preview
        preview_filename = None
        preview_url = None
        
        try:
            template = template_manager.get_template(original_entry.get('template'))
            label_size = template.get('size', '4x6') if template else '4x6'
            dpi = printer.get('dpi', 203)
            
            success, filename, error_msg = preview_generator.save_preview(
                rendered_zpl,
                filename=None,
                label_size=label_size,
                dpi=dpi,
                format='png'
            )
            
            if success:
                preview_filename = filename
                preview_url = f"/api/preview/{filename}"
                logger.info(f"Generated preview for reprint: {filename}")
            else:
                logger.warning(f"Failed to generate preview for reprint: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error generating preview for reprint: {str(e)}")
        
        # Send to printer
        send_success, send_msg = printer_manager.send_zpl(
            printer_id,
            rendered_zpl,
            quantity
        )
        
        if not send_success:
            return jsonify({
                'success': False,
                'error': send_msg
            }), 500
        
        # Create new history entry for reprint
        from datetime import datetime
        import uuid
        
        new_job_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        reprint_entry = {
            'id': new_job_id,
            'timestamp': timestamp,
            'template': original_entry.get('template'),
            'template_metadata': original_entry.get('template_metadata', {}),
            'printer_id': printer_id,
            'printer_name': printer.get('name', printer_id),
            'variables': variables,
            'quantity': quantity,
            'preview_filename': preview_filename,
            'status': 'success',
            'error_message': None,
            'rendered_zpl': rendered_zpl,
            'user': current_user.username,
            'reprint_of': entry_id
        }
        
        history_manager.add_entry(reprint_entry)
        
        logger.info(f"Reprint job {new_job_id} completed (original: {entry_id})")
        
        # Success response
        response_data = {
            'success': True,
            'message': f"Successfully reprinted {quantity} label(s)",
            'data': {
                'job_id': new_job_id,
                'original_job_id': entry_id,
                'printer_id': printer_id,
                'printer_name': printer.get('name', printer_id),
                'quantity': quantity,
                'timestamp': timestamp
            }
        }
        
        if preview_url:
            response_data['data']['preview_url'] = preview_url
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error reprinting from history {entry_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/search', methods=['GET'])
@login_required
def search_history():
    """
    Search history entries
    
    Query Parameters:
    - query: Search query string (required)
    - field: Specific field to search (optional)
    
    Response:
    {
        "success": true,
        "data": {
            "entries": [...],
            "count": 10
        }
    }
    """
    try:
        query = request.args.get('query')
        field = request.args.get('field')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter is required'
            }), 400
        
        entries = history_manager.search_entries(query, field)
        
        # Remove rendered_zpl from search results
        for entry in entries:
            entry.pop('rendered_zpl', None)
        
        return jsonify({
            'success': True,
            'data': {
                'entries': entries,
                'count': len(entries)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching history: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """
    Get usage statistics from history
    
    Query Parameters:
    - period: Time period for recent activity (default: 7 days)
    - grouping: Date grouping for volume ('day', 'week', 'month')
    
    Response:
    {
        "success": true,
        "data": {
            "overall": {...},
            "top_templates": [...],
            "top_printers": [...],
            "print_volume": {...},
            "success_rate": {...},
            "users": [...],
            "label_sizes": {...},
            "hourly_distribution": {...},
            "recent_activity": {...}
        }
    }
    """
    try:
        # Get query parameters
        period_days = request.args.get('period', 7, type=int)
        grouping = request.args.get('grouping', 'day')
        
        # Get all entries for statistics
        entries, _ = history_manager.get_entries(limit=500, offset=0)
        
        # Calculate various statistics
        overall_stats = calculate_print_statistics(entries)
        top_templates = get_top_templates(entries, limit=10)
        top_printers = get_top_printers(entries, limit=10)
        print_volume = get_print_volume_by_date(entries, grouping=grouping)
        success_rate = get_success_rate(entries)
        user_stats = get_user_statistics(entries)
        label_sizes = get_label_size_distribution(entries)
        hourly_dist = get_hourly_distribution(entries)
        recent_activity = get_recent_activity(entries, days=period_days)
        
        return jsonify({
            'success': True,
            'data': {
                'overall': overall_stats,
                'top_templates': top_templates,
                'top_printers': top_printers,
                'print_volume': print_volume,
                'success_rate': success_rate,
                'users': user_stats,
                'label_sizes': label_sizes,
                'hourly_distribution': hourly_dist,
                'recent_activity': recent_activity
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_old_entries():
    """
    Delete entries older than specified days
    
    Request JSON:
    {
        "days": 90  // Delete entries older than 90 days
    }
    
    Response:
    {
        "success": true,
        "message": "Deleted 25 old entries",
        "deleted_count": 25
    }
    """
    try:
        data = request.get_json() or {}
        days = data.get('days', 90)
        
        if not isinstance(days, int) or days < 1:
            return jsonify({
                'success': False,
                'error': 'Days must be a positive integer'
            }), 400
        
        success, deleted_count = history_manager.cleanup_old_entries(days)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to cleanup old entries'
            }), 500
        
        logger.info(f"User {current_user.username} cleaned up {deleted_count} entries older than {days} days")
        
        return jsonify({
            'success': True,
            'message': f"Deleted {deleted_count} old entries",
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up old entries: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500


@history_bp.route('/export', methods=['GET'])
@login_required
def export_history():
    """
    Export history to specified format
    
    Query Parameters:
    - format: Export format ('json' or 'csv', default: 'json')
    
    Response:
    - JSON: Returns JSON array of entries
    - CSV: Returns CSV file
    """
    try:
        export_format = request.args.get('format', 'json').lower()
        
        if export_format not in ['json', 'csv']:
            return jsonify({
                'success': False,
                'error': 'Format must be "json" or "csv"'
            }), 400
        
        success, data = history_manager.export_history(format=export_format)
        
        if not success:
            return jsonify({
                'success': False,
                'error': data
            }), 500
        
        logger.info(f"User {current_user.username} exported history as {export_format}")
        
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': data
            }), 200
        else:  # csv
            from flask import Response
            return Response(
                data,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': 'attachment; filename=history_export.csv'
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting history: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Internal server error: {str(e)}"
        }), 500