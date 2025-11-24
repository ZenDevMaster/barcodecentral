"""
Web UI Blueprint
Handles all web page routes (dashboard, templates, print, history, printers)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from template_manager import TemplateManager
from printer_manager import PrinterManager
from history_manager import HistoryManager
import os
import logging

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)

# Initialize managers
template_manager = TemplateManager()
printer_manager = PrinterManager()
history_manager = HistoryManager()


@web_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    try:
        # Get statistics
        templates = template_manager.list_templates()
        printers = printer_manager.list_printers()
        history, _ = history_manager.get_entries(limit=10)
        
        # Calculate statistics
        all_history, total_prints = history_manager.get_entries(limit=1000)
        active_printers = len([p for p in printers if p.get('enabled', True)])
        
        stats = {
            'total_prints': total_prints,
            'total_templates': len(templates),
            'active_printers': active_printers,
            'recent_history': history
        }
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', stats={})


@web_bp.route('/templates')
@login_required
def templates():
    """Template management page"""
    try:
        templates_list = template_manager.list_templates()
        logger.info(f"Loading templates page with {len(templates_list)} templates")
        return render_template('templates.html', templates=templates_list)
    except Exception as e:
        logger.error(f'Error loading templates page: {str(e)}', exc_info=True)
        flash(f'Error loading templates: {str(e)}', 'danger')
        return render_template('templates.html', templates=[])


@web_bp.route('/templates/new')
@login_required
def new_template():
    """Create new template page"""
    # Provide a starter ZPL template
    starter_zpl = """^XA
^FO50,50^A0N,50,50^FDHello World^FS
^XZ"""
    return render_template('new_template.html', starter_zpl=starter_zpl)


@web_bp.route('/templates/<name>/edit')
@login_required
def edit_template(name):
    """Edit template page"""
    try:
        template = template_manager.get_template(name)
        if not template:
            flash(f'Template "{name}" not found.', 'danger')
            return redirect(url_for('web.templates'))
        
        # Get ZPL content directly from template
        zpl_content = template.get('content', '')
        
        return render_template('edit_template.html', template=template, zpl_content=zpl_content)
    except Exception as e:
        flash(f'Error loading template: {str(e)}', 'danger')
        return redirect(url_for('web.templates'))


@web_bp.route('/print')
@login_required
def print_form():
    """Print form page"""
    try:
        templates_list = template_manager.list_templates()
        printers_list = printer_manager.list_printers()
        
        # Get selected template if specified
        selected_template = request.args.get('template')
        template_data = None
        if selected_template:
            logger.info(f"Loading print form with pre-selected template: {selected_template}")
            template_data = template_manager.get_template(selected_template)
        
        logger.info(f"Loading print form with {len(templates_list)} templates and {len(printers_list)} printers")
        return render_template('print_form.html',
                             templates=templates_list,
                             printers=printers_list,
                             selected_template=template_data)
    except Exception as e:
        logger.error(f'Error loading print form: {str(e)}', exc_info=True)
        flash(f'Error loading print form: {str(e)}', 'danger')
        return render_template('print_form.html', templates=[], printers=[])


@web_bp.route('/history')
@login_required
def history():
    """History page"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get filter parameters
        template_filter = request.args.get('template')
        printer_filter = request.args.get('printer')
        status_filter = request.args.get('status')
        
        # Get history with filters
        all_history, _ = history_manager.get_entries(limit=1000)
        
        # Apply filters
        filtered_history = all_history
        if template_filter:
            filtered_history = [h for h in filtered_history if h.get('template_name') == template_filter]
        if printer_filter:
            filtered_history = [h for h in filtered_history if h.get('printer_name') == printer_filter]
        if status_filter:
            filtered_history = [h for h in filtered_history if h.get('status') == status_filter]
        
        # Calculate pagination
        total = len(filtered_history)
        start = (page - 1) * per_page
        end = start + per_page
        history_page = filtered_history[start:end]
        
        # Get unique values for filters
        templates_list = list(set([h.get('template_name') for h in all_history if h.get('template_name')]))
        printers_list = list(set([h.get('printer_name') for h in all_history if h.get('printer_name')]))
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
        
        return render_template('history.html', 
                             history=history_page,
                             pagination=pagination,
                             templates=templates_list,
                             printers=printers_list,
                             filters={
                                 'template': template_filter,
                                 'printer': printer_filter,
                                 'status': status_filter
                             })
    except Exception as e:
        flash(f'Error loading history: {str(e)}', 'danger')
        return render_template('history.html',
                             history=[],
                             pagination={},
                             templates=[],
                             printers=[],
                             filters={'template': '', 'printer': '', 'status': ''})


@web_bp.route('/printers')
@login_required
def printers():
    """Printer management page"""
    try:
        # Force reload to ensure fresh data after updates
        printer_manager._printers_cache = None
        printers_list = printer_manager.list_printers()
        return render_template('printers.html', printers=printers_list)
    except Exception as e:
        flash(f'Error loading printers: {str(e)}', 'danger')
        return render_template('printers.html', printers=[])