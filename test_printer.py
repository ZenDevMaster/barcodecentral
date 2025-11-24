#!/usr/bin/env python3
"""
Test script for printer communication
Usage: python test_printer.py <printer_id> [--test-connection] [--send-test-label]
"""
import sys
import argparse
from printer_manager import PrinterManager
from template_manager import TemplateManager
from print_job import create_print_job, execute_print_job


def list_printers():
    """List all configured printers"""
    print("\n=== Configured Printers ===\n")
    
    manager = PrinterManager()
    printers = manager.list_printers()
    
    if not printers:
        print("No printers configured.")
        return
    
    for printer in printers:
        print(f"ID: {printer['id']}")
        print(f"  Name: {printer['name']}")
        print(f"  IP: {printer['ip']}:{printer['port']}")
        print(f"  Supported Sizes: {', '.join(printer['supported_sizes'])}")
        print(f"  DPI: {printer['dpi']}")
        print(f"  Enabled: {printer['enabled']}")
        if 'location' in printer:
            print(f"  Location: {printer['location']}")
        print()


def test_connection(printer_id):
    """Test printer connection"""
    print(f"\n=== Testing Connection to {printer_id} ===\n")
    
    manager = PrinterManager()
    
    # Get printer details
    printer = manager.get_printer(printer_id)
    if not printer:
        print(f"ERROR: Printer '{printer_id}' not found")
        return False
    
    print(f"Printer: {printer['name']}")
    print(f"IP: {printer['ip']}:{printer['port']}")
    print(f"Testing connection...")
    
    # Test connection
    success, message = manager.test_printer_connection(printer_id, timeout=5)
    
    if success:
        print(f"✓ SUCCESS: {message}")
        return True
    else:
        print(f"✗ FAILED: {message}")
        return False


def send_test_label(printer_id):
    """Send a test ZPL label to printer"""
    print(f"\n=== Sending Test Label to {printer_id} ===\n")
    
    manager = PrinterManager()
    
    # Get printer details
    printer = manager.get_printer(printer_id)
    if not printer:
        print(f"ERROR: Printer '{printer_id}' not found")
        return False
    
    print(f"Printer: {printer['name']}")
    print(f"IP: {printer['ip']}:{printer['port']}")
    
    # Create simple test ZPL
    test_zpl = """^XA
^FO50,50^A0N,50,50^FDTest Label^FS
^FO50,120^A0N,30,30^FDPrinter: {printer_name}^FS
^FO50,170^A0N,30,30^FDIP: {printer_ip}^FS
^FO50,220^A0N,30,30^FDTimestamp: {timestamp}^FS
^FO50,300^BY3^BCN,100,Y,N,N^FD123456789^FS
^XZ""".format(
        printer_name=printer['name'],
        printer_ip=printer['ip'],
        timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    print("Sending test label...")
    print(f"ZPL Preview:\n{test_zpl[:200]}...\n")
    
    # Send ZPL
    success, message = manager.send_zpl(printer_id, test_zpl, quantity=1)
    
    if success:
        print(f"✓ SUCCESS: {message}")
        return True
    else:
        print(f"✗ FAILED: {message}")
        return False


def validate_printer(printer_id, label_size):
    """Validate printer configuration and compatibility"""
    print(f"\n=== Validating Printer {printer_id} ===\n")
    
    manager = PrinterManager()
    
    # Get printer details
    printer = manager.get_printer(printer_id)
    if not printer:
        print(f"ERROR: Printer '{printer_id}' not found")
        return False
    
    print(f"Printer: {printer['name']}")
    print(f"IP: {printer['ip']}:{printer['port']}")
    print(f"Enabled: {printer['enabled']}")
    print(f"Supported Sizes: {', '.join(printer['supported_sizes'])}")
    print()
    
    # Test connection
    print("Testing connection...")
    conn_success, conn_msg = manager.test_printer_connection(printer_id, timeout=5)
    if conn_success:
        print(f"  ✓ Connection: {conn_msg}")
    else:
        print(f"  ✗ Connection: {conn_msg}")
    
    # Test compatibility if label size provided
    if label_size:
        print(f"\nTesting compatibility with label size '{label_size}'...")
        compat_success, compat_msg = manager.validate_printer_compatibility(printer_id, label_size)
        if compat_success:
            print(f"  ✓ Compatibility: {compat_msg}")
        else:
            print(f"  ✗ Compatibility: {compat_msg}")
    
    print()
    return conn_success


def test_print_job(printer_id, template_name):
    """Test complete print job workflow"""
    print(f"\n=== Testing Print Job ===\n")
    print(f"Printer: {printer_id}")
    print(f"Template: {template_name}")
    
    # Get template to see required variables
    template_manager = TemplateManager()
    template = template_manager.get_template(template_name)
    
    if not template:
        print(f"ERROR: Template '{template_name}' not found")
        return False
    
    print(f"Template Name: {template.get('name', template_name)}")
    print(f"Label Size: {template.get('label_size', 'unknown')}")
    print(f"Required Variables: {', '.join(template.get('variables', []))}")
    print()
    
    # Create sample variables
    variables = {}
    for var in template.get('variables', []):
        variables[var] = f"TEST_{var.upper()}"
    
    print(f"Using test variables: {variables}")
    print()
    
    # Create and execute print job
    print("Creating print job...")
    job = create_print_job(template_name, printer_id, variables, quantity=1)
    
    print("Validating print job...")
    is_valid, validation_msg = job.validate()
    if not is_valid:
        print(f"✗ Validation failed: {validation_msg}")
        return False
    print(f"✓ Validation passed")
    
    print("\nRendering template...")
    render_success, render_result = job.render()
    if not render_success:
        print(f"✗ Rendering failed: {render_result}")
        return False
    print(f"✓ Template rendered successfully")
    print(f"ZPL Preview:\n{render_result[:200]}...\n")
    
    # Ask for confirmation before printing
    response = input("Send to printer? (y/n): ")
    if response.lower() != 'y':
        print("Print job cancelled")
        return False
    
    print("\nExecuting print job...")
    success, message, job_dict = execute_print_job(job)
    
    if success:
        print(f"✓ SUCCESS: {message}")
        print(f"\nJob Details:")
        print(f"  Status: {job_dict['status']}")
        print(f"  Timestamp: {job_dict['timestamp']}")
        return True
    else:
        print(f"✗ FAILED: {message}")
        print(f"\nJob Details:")
        print(f"  Status: {job_dict['status']}")
        print(f"  Error: {job_dict['error']}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test printer communication and functionality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_printer.py --list
  python test_printer.py zebra-warehouse-01 --test-connection
  python test_printer.py zebra-warehouse-01 --send-test-label
  python test_printer.py zebra-warehouse-01 --validate --label-size 4x6
  python test_printer.py zebra-warehouse-01 --print-job --template example.zpl.j2
        """
    )
    
    parser.add_argument('printer_id', nargs='?', help='Printer ID to test')
    parser.add_argument('--list', action='store_true', help='List all configured printers')
    parser.add_argument('--test-connection', action='store_true', help='Test printer connection')
    parser.add_argument('--send-test-label', action='store_true', help='Send a test label to printer')
    parser.add_argument('--validate', action='store_true', help='Validate printer configuration')
    parser.add_argument('--label-size', help='Label size for validation (e.g., 4x6)')
    parser.add_argument('--print-job', action='store_true', help='Test complete print job workflow')
    parser.add_argument('--template', help='Template name for print job test')
    
    args = parser.parse_args()
    
    # List printers
    if args.list:
        list_printers()
        return 0
    
    # Require printer_id for other operations
    if not args.printer_id:
        parser.print_help()
        return 1
    
    # Execute requested operation
    success = True
    
    if args.test_connection:
        success = test_connection(args.printer_id)
    
    elif args.send_test_label:
        success = send_test_label(args.printer_id)
    
    elif args.validate:
        success = validate_printer(args.printer_id, args.label_size)
    
    elif args.print_job:
        if not args.template:
            print("ERROR: --template is required for --print-job")
            return 1
        success = test_print_job(args.printer_id, args.template)
    
    else:
        # Default: test connection
        success = test_connection(args.printer_id)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())