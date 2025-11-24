"""
Print Job Module for Barcode Central
Handles complete print job workflow: validation, rendering, and execution
"""
import logging
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from template_manager import TemplateManager
from printer_manager import PrinterManager

# Configure logging
logger = logging.getLogger(__name__)


class PrintJob:
    """Represents a complete print job with template, printer, and variables"""
    
    def __init__(
        self,
        template_name: str,
        printer_id: str,
        variables: Dict[str, Any],
        quantity: int = 1,
        generate_preview: bool = False,
        log_to_history: bool = True,
        user: str = 'unknown'
    ):
        """
        Initialize a print job
        
        Args:
            template_name: Name of the ZPL template file
            printer_id: ID of the printer to use
            variables: Dictionary of variables to render in template
            quantity: Number of copies to print (1-100)
            generate_preview: Whether to generate preview image
            log_to_history: Whether to log this job to history (default: True)
            user: Username of the user executing the job
        """
        self.job_id = str(uuid.uuid4())
        self.template_name = template_name
        self.printer_id = printer_id
        self.variables = variables if variables else {}
        self.quantity = quantity
        self.generate_preview = generate_preview
        self.log_to_history = log_to_history
        self.user = user
        self.rendered_zpl = None
        self.preview_filename = None
        self.preview_url = None
        self.validation_errors = []
        self.status = 'pending'
        self.error_message = None
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Initialize managers
        self.template_manager = TemplateManager()
        self.printer_manager = PrinterManager()
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate all components of the print job
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        self.validation_errors = []
        
        # Validate quantity
        if not isinstance(self.quantity, int) or self.quantity < 1 or self.quantity > 100:
            self.validation_errors.append("Quantity must be between 1 and 100")
        
        # Validate template exists
        template = self.template_manager.get_template(self.template_name)
        if not template:
            self.validation_errors.append(f"Template '{self.template_name}' not found")
            return False, "; ".join(self.validation_errors)
        
        # Validate printer exists
        printer = self.printer_manager.get_printer(self.printer_id)
        if not printer:
            self.validation_errors.append(f"Printer '{self.printer_id}' not found")
            return False, "; ".join(self.validation_errors)
        
        # Check if printer is enabled
        if not printer.get('enabled', True):
            self.validation_errors.append(f"Printer '{self.printer_id}' is disabled")
            return False, "; ".join(self.validation_errors)
        
        # Validate compatibility (label size)
        label_size = template.get('label_size', '')
        if label_size:
            is_compatible, compat_msg = self.printer_manager.validate_printer_compatibility(
                self.printer_id, label_size
            )
            if not is_compatible:
                self.validation_errors.append(compat_msg)
                return False, "; ".join(self.validation_errors)
        
        # Check for required variables
        required_vars = template.get('variables', [])
        missing_vars = [var for var in required_vars if var not in self.variables]
        if missing_vars:
            self.validation_errors.append(f"Missing required variables: {', '.join(missing_vars)}")
            return False, "; ".join(self.validation_errors)
        
        # All validations passed
        if self.validation_errors:
            return False, "; ".join(self.validation_errors)
        
        return True, "Validation successful"
    
    def render(self) -> Tuple[bool, str]:
        """
        Render the template with variables to generate ZPL
        
        Returns:
            Tuple of (success, message_or_zpl)
        """
        try:
            # Render template
            success, result = self.template_manager.render_template(
                self.template_name, 
                self.variables
            )
            
            if not success:
                self.status = 'failed'
                self.error_message = result
                logger.error(f"Failed to render template '{self.template_name}': {result}")
                return False, result
            
            self.rendered_zpl = result
            logger.info(f"Successfully rendered template '{self.template_name}'")
            return True, result
            
        except Exception as e:
            error_msg = f"Error rendering template: {str(e)}"
            self.status = 'failed'
            self.error_message = error_msg
            logger.error(f"Print job render error: {error_msg}")
            return False, error_msg
    
    def generate_preview_image(self) -> Tuple[bool, str]:
        """
        Generate preview image from rendered ZPL
        
        Returns:
            Tuple of (success, message_or_filename)
        """
        if not self.rendered_zpl:
            return False, "No rendered ZPL available. Call render() first."
        
        try:
            # Import here to avoid circular dependency
            from preview_generator import PreviewGenerator
            
            preview_gen = PreviewGenerator()
            
            # Get template and printer details for label size and DPI
            template = self.template_manager.get_template(self.template_name)
            printer = self.printer_manager.get_printer(self.printer_id)
            
            label_size = template.get('size', '4x6')
            dpi = printer.get('dpi', 203) if printer else 203
            
            # Generate and save preview
            success, filename, error_msg = preview_gen.save_preview(
                self.rendered_zpl,
                filename=None,  # Auto-generate UUID filename
                label_size=label_size,
                dpi=dpi,
                format='png'
            )
            
            if success:
                self.preview_filename = filename
                self.preview_url = f"/api/preview/{filename}"
                logger.info(f"Generated preview for print job: {filename}")
                return True, filename
            else:
                logger.warning(f"Failed to generate preview: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error generating preview: {str(e)}"
            logger.error(f"Print job preview error: {error_msg}")
            return False, error_msg
    
    def execute(self) -> Tuple[bool, str]:
        """
        Execute the complete print job: validate, render, and send to printer
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Step 1: Validate
            is_valid, validation_msg = self.validate()
            if not is_valid:
                self.status = 'failed'
                self.error_message = validation_msg
                logger.warning(f"Print job validation failed: {validation_msg}")
                
                # Log failed validation to history
                if self.log_to_history:
                    self._log_to_history()
                
                return False, validation_msg
            
            # Step 2: Render
            render_success, render_result = self.render()
            if not render_success:
                # Log failed render to history
                if self.log_to_history:
                    self._log_to_history()
                
                return False, render_result
            
            # Step 3: Generate preview (if requested)
            if self.generate_preview:
                preview_success, preview_result = self.generate_preview_image()
                if not preview_success:
                    # Log warning but don't fail the print job
                    logger.warning(f"Preview generation failed: {preview_result}")
            
            # Step 4: Send to printer
            send_success, send_msg = self.printer_manager.send_zpl(
                self.printer_id,
                self.rendered_zpl,
                self.quantity
            )
            
            if not send_success:
                self.status = 'failed'
                self.error_message = send_msg
                logger.error(f"Failed to send to printer '{self.printer_id}': {send_msg}")
                
                # Log failed print to history
                if self.log_to_history:
                    self._log_to_history()
                
                return False, send_msg
            
            # Success
            self.status = 'success'
            logger.info(f"Print job {self.job_id} completed successfully: {self.template_name} -> {self.printer_id} (x{self.quantity})")
            
            # Log successful print to history
            if self.log_to_history:
                self._log_to_history()
            
            return True, f"Successfully printed {self.quantity} label(s)"
            
        except Exception as e:
            error_msg = f"Unexpected error executing print job: {str(e)}"
            self.status = 'failed'
            self.error_message = error_msg
            logger.error(f"Print job execution error: {error_msg}")
            
            # Log exception to history
            if self.log_to_history:
                self._log_to_history()
            
            return False, error_msg
    
    def _log_to_history(self) -> None:
        """
        Log this print job to history
        """
        try:
            from history_manager import HistoryManager
            history_manager = HistoryManager()
            
            # Get template and printer details
            template = self.template_manager.get_template(self.template_name)
            printer = self.printer_manager.get_printer(self.printer_id)
            
            # Create history entry
            entry = {
                'id': self.job_id,
                'timestamp': self.timestamp,
                'template': self.template_name,
                'template_metadata': {
                    'name': template.get('name', self.template_name) if template else self.template_name,
                    'size': template.get('size', 'unknown') if template else 'unknown'
                },
                'printer_id': self.printer_id,
                'printer_name': printer.get('name', self.printer_id) if printer else self.printer_id,
                'variables': self.variables,
                'quantity': self.quantity,
                'preview_filename': self.preview_filename,
                'status': self.status,
                'error_message': self.error_message,
                'rendered_zpl': self.rendered_zpl,
                'user': self.user
            }
            
            success, result = history_manager.add_entry(entry)
            if success:
                logger.debug(f"Logged print job {self.job_id} to history")
            else:
                logger.warning(f"Failed to log print job to history: {result}")
                
        except Exception as e:
            logger.error(f"Error logging to history: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert print job to dictionary for API responses
        
        Returns:
            Dictionary representation of the print job
        """
        # Get template and printer details
        template = self.template_manager.get_template(self.template_name)
        printer = self.printer_manager.get_printer(self.printer_id)
        
        job_dict = {
            'job_id': self.job_id,
            'timestamp': self.timestamp,
            'template': self.template_name,
            'template_name': template.get('name', self.template_name) if template else self.template_name,
            'printer_id': self.printer_id,
            'printer_name': printer.get('name', self.printer_id) if printer else self.printer_id,
            'printer_ip': printer.get('ip', 'unknown') if printer else 'unknown',
            'variables': self.variables,
            'quantity': self.quantity,
            'label_size': template.get('size', 'unknown') if template else 'unknown',
            'status': self.status,
            'error': self.error_message,
            'user': self.user
        }
        
        # Add preview information if available
        if self.preview_filename:
            job_dict['preview_filename'] = self.preview_filename
        if self.preview_url:
            job_dict['preview_url'] = self.preview_url
        
        return job_dict


def create_print_job(
    template_name: str,
    printer_id: str,
    variables: Dict[str, Any],
    quantity: int = 1,
    generate_preview: bool = False,
    log_to_history: bool = True,
    user: str = 'unknown'
) -> PrintJob:
    """
    Factory function to create a print job
    
    Args:
        template_name: Name of the ZPL template file
        printer_id: ID of the printer to use
        variables: Dictionary of variables to render in template
        quantity: Number of copies to print (1-100)
        generate_preview: Whether to generate preview image
        log_to_history: Whether to log this job to history
        user: Username of the user executing the job
        
    Returns:
        PrintJob instance
    """
    return PrintJob(template_name, printer_id, variables, quantity, generate_preview, log_to_history, user)


def execute_print_job(job: PrintJob) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Execute a print job and return detailed results
    
    Args:
        job: PrintJob instance to execute
        
    Returns:
        Tuple of (success, message, job_dict)
    """
    success, message = job.execute()
    job_dict = job.to_dict()
    
    return success, message, job_dict