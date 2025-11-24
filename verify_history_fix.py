#!/usr/bin/env python3
"""
Verification script for history display fix
Tests that template names and user information are correctly displayed
"""

from history_manager import HistoryManager

def verify_history_data():
    """Verify that history entries have the correct fields"""
    print("=" * 60)
    print("HISTORY DATA VERIFICATION")
    print("=" * 60)
    
    hm = HistoryManager()
    entries, total = hm.get_entries(limit=5)
    
    if not entries:
        print("❌ No history entries found")
        return False
    
    print(f"\n✓ Found {total} total history entries")
    print(f"✓ Displaying first {len(entries)} entries:\n")
    
    all_good = True
    
    for i, entry in enumerate(entries, 1):
        print(f"Entry {i}:")
        print(f"  ID: {entry.get('id', 'N/A')}")
        print(f"  Timestamp: {entry.get('timestamp', 'N/A')}")
        
        # Check template field
        template = entry.get('template')
        template_metadata = entry.get('template_metadata', {})
        template_name = template_metadata.get('name', template)
        
        if template:
            print(f"  ✓ Template (filename): {template}")
            print(f"  ✓ Template (display name): {template_name}")
        else:
            print(f"  ❌ Template field missing!")
            all_good = False
        
        # Check user field
        user = entry.get('user')
        if user:
            print(f"  ✓ User: {user}")
        else:
            print(f"  ❌ User field missing!")
            all_good = False
        
        # Check printer field
        printer_name = entry.get('printer_name')
        if printer_name:
            print(f"  ✓ Printer: {printer_name}")
        else:
            print(f"  ❌ Printer name missing!")
            all_good = False
        
        print(f"  Status: {entry.get('status', 'N/A')}")
        print(f"  Quantity: {entry.get('quantity', 'N/A')}")
        print()
    
    print("=" * 60)
    if all_good:
        print("✓ ALL CHECKS PASSED - History data is correct!")
    else:
        print("❌ SOME CHECKS FAILED - Review the output above")
    print("=" * 60)
    
    return all_good

if __name__ == '__main__':
    verify_history_data()