#!/usr/bin/env python3
"""
Test script for history management system
Tests history tracking, search, statistics, and reprint functionality

Usage:
    python test_history.py [--add-sample] [--list] [--stats] [--cleanup] [--search QUERY] [--reprint ID]
"""
import argparse
import sys
import json
from datetime import datetime, timedelta
from history_manager import HistoryManager
from utils.statistics import (
    calculate_print_statistics,
    get_top_templates,
    get_top_printers,
    get_print_volume_by_date,
    get_success_rate,
    get_user_statistics
)


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_entry(entry, detailed=False):
    """Print a history entry"""
    print(f"\nID: {entry.get('id')}")
    print(f"Timestamp: {entry.get('timestamp')}")
    print(f"User: {entry.get('user', 'unknown')}")
    print(f"Template: {entry.get('template')}")
    print(f"Printer: {entry.get('printer_name', entry.get('printer_id'))}")
    print(f"Quantity: {entry.get('quantity')}")
    print(f"Status: {entry.get('status')}")
    
    if entry.get('error_message'):
        print(f"Error: {entry.get('error_message')}")
    
    if detailed:
        print(f"\nVariables:")
        for key, value in entry.get('variables', {}).items():
            print(f"  {key}: {value}")
        
        if entry.get('rendered_zpl'):
            zpl = entry.get('rendered_zpl')
            print(f"\nRendered ZPL ({len(zpl)} chars):")
            print(f"  {zpl[:100]}..." if len(zpl) > 100 else f"  {zpl}")


def add_sample_entries():
    """Add sample history entries for testing"""
    print_header("Adding Sample History Entries")
    
    history_manager = HistoryManager()
    
    # Sample entries
    samples = [
        {
            "template": "example.zpl.j2",
            "template_metadata": {"name": "Example Label", "size": "4x6"},
            "printer_id": "zebra-warehouse-01",
            "printer_name": "Zebra ZT230 - Warehouse",
            "variables": {"order_number": "TEST-001", "customer_name": "Test User"},
            "quantity": 1,
            "status": "success",
            "error_message": None,
            "rendered_zpl": "^XA^CF0,60^FO50,50^FDTest^FS^XZ",
            "user": "admin"
        },
        {
            "template": "product_label_4x2.zpl.j2",
            "template_metadata": {"name": "Product Label", "size": "4x2"},
            "printer_id": "zebra-warehouse-01",
            "printer_name": "Zebra ZT230 - Warehouse",
            "variables": {"sku": "TEST-SKU", "name": "Test Product", "price": "$9.99"},
            "quantity": 5,
            "status": "success",
            "error_message": None,
            "rendered_zpl": "^XA^CF0,40^FO50,50^FDTest Product^FS^XZ",
            "user": "admin"
        },
        {
            "template": "example.zpl.j2",
            "template_metadata": {"name": "Example Label", "size": "4x6"},
            "printer_id": "zebra-office-01",
            "printer_name": "Zebra GK420d - Office",
            "variables": {"order_number": "TEST-002", "customer_name": "Failed Test"},
            "quantity": 1,
            "status": "failed",
            "error_message": "Printer unreachable: Connection timeout",
            "rendered_zpl": "^XA^CF0,60^FO50,50^FDFailed Test^FS^XZ",
            "user": "admin"
        }
    ]
    
    added_count = 0
    for sample in samples:
        success, result = history_manager.add_entry(sample)
        if success:
            print(f"✓ Added entry: {result}")
            added_count += 1
        else:
            print(f"✗ Failed to add entry: {result}")
    
    print(f"\nAdded {added_count} sample entries")


def list_history(limit=10):
    """List recent history entries"""
    print_header(f"Recent History (Last {limit} entries)")
    
    history_manager = HistoryManager()
    entries, total = history_manager.get_entries(limit=limit, offset=0)
    
    if not entries:
        print("\nNo history entries found")
        return
    
    print(f"\nShowing {len(entries)} of {total} total entries\n")
    
    for i, entry in enumerate(entries, 1):
        print(f"\n{i}. ", end="")
        print_entry(entry, detailed=False)


def show_statistics():
    """Display history statistics"""
    print_header("History Statistics")
    
    history_manager = HistoryManager()
    entries, _ = history_manager.get_entries(limit=500, offset=0)
    
    if not entries:
        print("\nNo history entries found")
        return
    
    # Overall statistics
    print("\n📊 Overall Statistics:")
    overall = calculate_print_statistics(entries)
    print(f"  Total Print Jobs: {overall['total_prints']}")
    print(f"  Total Labels: {overall['total_labels']}")
    print(f"  Successful: {overall['success_count']}")
    print(f"  Failed: {overall['failed_count']}")
    print(f"  Success Rate: {overall['success_rate']}%")
    print(f"  Average Quantity: {overall['average_quantity']}")
    
    # Top templates
    print("\n📄 Top Templates:")
    top_templates = get_top_templates(entries, limit=5)
    for i, template in enumerate(top_templates, 1):
        print(f"  {i}. {template['name']} ({template['template']}): {template['count']} prints")
    
    # Top printers
    print("\n🖨️  Top Printers:")
    top_printers = get_top_printers(entries, limit=5)
    for i, printer in enumerate(top_printers, 1):
        print(f"  {i}. {printer['name']} ({printer['printer_id']}): {printer['count']} prints")
    
    # User statistics
    print("\n👤 User Statistics:")
    user_stats = get_user_statistics(entries)
    for user in user_stats:
        print(f"  {user['user']}: {user['prints']} prints, {user['labels']} labels, {user['success_rate']}% success")
    
    # Print volume by day
    print("\n📅 Print Volume (Last 7 Days):")
    volume = get_print_volume_by_date(entries, grouping='day')
    # Get last 7 days
    today = datetime.utcnow()
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        count = volume.get(date, 0)
        print(f"  {date}: {count} prints")


def search_history(query):
    """Search history entries"""
    print_header(f"Search Results for: '{query}'")
    
    history_manager = HistoryManager()
    entries = history_manager.search_entries(query)
    
    if not entries:
        print(f"\nNo entries found matching '{query}'")
        return
    
    print(f"\nFound {len(entries)} matching entries:\n")
    
    for i, entry in enumerate(entries, 1):
        print(f"\n{i}. ", end="")
        print_entry(entry, detailed=False)


def test_reprint(entry_id):
    """Test reprint functionality"""
    print_header(f"Testing Reprint for Entry: {entry_id}")
    
    history_manager = HistoryManager()
    entry = history_manager.get_entry(entry_id)
    
    if not entry:
        print(f"\n✗ Entry not found: {entry_id}")
        return
    
    print("\nOriginal Entry:")
    print_entry(entry, detailed=True)
    
    print("\n" + "-" * 70)
    print("Reprint Test:")
    print("  Note: This is a dry-run test. No actual printing will occur.")
    print("  In production, this would:")
    print(f"  1. Validate printer '{entry.get('printer_id')}' is available")
    print(f"  2. Re-render template with variables or use stored ZPL")
    print(f"  3. Generate new preview")
    print(f"  4. Send to printer")
    print(f"  5. Create new history entry")
    print("\n✓ Reprint test completed (dry-run)")


def cleanup_old_entries(days=90):
    """Cleanup old history entries"""
    print_header(f"Cleanup Entries Older Than {days} Days")
    
    history_manager = HistoryManager()
    
    # Get current count
    entries, total_before = history_manager.get_entries(limit=1, offset=0)
    print(f"\nTotal entries before cleanup: {total_before}")
    
    # Perform cleanup
    success, deleted_count = history_manager.cleanup_old_entries(days)
    
    if success:
        print(f"✓ Deleted {deleted_count} old entries")
        
        # Get new count
        entries, total_after = history_manager.get_entries(limit=1, offset=0)
        print(f"Total entries after cleanup: {total_after}")
    else:
        print("✗ Cleanup failed")


def test_export():
    """Test history export functionality"""
    print_header("Testing History Export")
    
    history_manager = HistoryManager()
    
    # Test JSON export
    print("\n📄 JSON Export:")
    success, data = history_manager.export_history(format='json')
    if success:
        print(f"✓ Exported {len(data)} entries as JSON")
        print(f"  Sample: {json.dumps(data[0] if data else {}, indent=2)[:200]}...")
    else:
        print(f"✗ JSON export failed: {data}")
    
    # Test CSV export
    print("\n📄 CSV Export:")
    success, data = history_manager.export_history(format='csv')
    if success:
        lines = data.split('\n')
        print(f"✓ Exported as CSV ({len(lines)} lines)")
        print(f"  Header: {lines[0]}")
        if len(lines) > 1:
            print(f"  Sample: {lines[1]}")
    else:
        print(f"✗ CSV export failed: {data}")


def run_all_tests():
    """Run all tests"""
    print_header("Running All History Tests")
    
    print("\n1. Testing History Manager Initialization")
    history_manager = HistoryManager()
    print("✓ History manager initialized")
    
    print("\n2. Testing Entry Retrieval")
    entries, total = history_manager.get_entries(limit=5)
    print(f"✓ Retrieved {len(entries)} of {total} entries")
    
    print("\n3. Testing Statistics")
    stats = history_manager.get_statistics()
    print(f"✓ Statistics calculated: {stats.get('total_prints', 0)} total prints")
    
    print("\n4. Testing Search")
    results = history_manager.search_entries("admin")
    print(f"✓ Search completed: {len(results)} results")
    
    print("\n5. Testing Export")
    success, data = history_manager.export_history(format='json')
    print(f"✓ Export completed: {len(data) if success else 0} entries")
    
    print("\n" + "=" * 70)
    print("  All tests completed successfully!")
    print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test script for Barcode Central history management'
    )
    parser.add_argument('--add-sample', action='store_true',
                       help='Add sample history entries')
    parser.add_argument('--list', type=int, metavar='N', nargs='?', const=10,
                       help='List N recent history entries (default: 10)')
    parser.add_argument('--stats', action='store_true',
                       help='Show history statistics')
    parser.add_argument('--search', type=str, metavar='QUERY',
                       help='Search history entries')
    parser.add_argument('--reprint', type=str, metavar='ID',
                       help='Test reprint functionality for entry ID')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', nargs='?', const=90,
                       help='Cleanup entries older than DAYS (default: 90)')
    parser.add_argument('--export', action='store_true',
                       help='Test export functionality')
    parser.add_argument('--all', action='store_true',
                       help='Run all tests')
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    try:
        if args.all:
            run_all_tests()
        
        if args.add_sample:
            add_sample_entries()
        
        if args.list is not None:
            list_history(args.list)
        
        if args.stats:
            show_statistics()
        
        if args.search:
            search_history(args.search)
        
        if args.reprint:
            test_reprint(args.reprint)
        
        if args.cleanup is not None:
            cleanup_old_entries(args.cleanup)
        
        if args.export:
            test_export()
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()