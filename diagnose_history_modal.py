#!/usr/bin/env python3
"""
Diagnostic script to test history modal functionality
"""
import json
import os
from history_manager import HistoryManager

def diagnose_history_modal():
    """Diagnose why the history modal might be empty"""
    
    print("=" * 60)
    print("HISTORY MODAL DIAGNOSTIC")
    print("=" * 60)
    
    # Check if history file exists
    history_file = 'history.json'
    print(f"\n1. Checking history file: {history_file}")
    if not os.path.exists(history_file):
        print(f"   ❌ History file does not exist!")
        return
    else:
        print(f"   ✓ History file exists")
    
    # Load history data
    print("\n2. Loading history data...")
    try:
        with open(history_file, 'r') as f:
            data = json.load(f)
        print(f"   ✓ Successfully loaded history file")
        print(f"   - Total entries: {len(data.get('entries', []))}")
    except Exception as e:
        print(f"   ❌ Error loading history: {e}")
        return
    
    # Check if there are entries
    entries = data.get('entries', [])
    if not entries:
        print("\n   ⚠️  No history entries found!")
        print("   This is why the modal is empty - there's no data to display.")
        return
    
    # Show sample entry structure
    print("\n3. Analyzing first entry structure...")
    first_entry = entries[0]
    print(f"   Entry ID: {first_entry.get('id', 'MISSING')}")
    print(f"   Fields present:")
    for key in sorted(first_entry.keys()):
        value = first_entry[key]
        if isinstance(value, str) and len(value) > 50:
            print(f"     - {key}: <{len(value)} chars>")
        else:
            print(f"     - {key}: {value}")
    
    # Test HistoryManager.get_entry()
    print("\n4. Testing HistoryManager.get_entry()...")
    hm = HistoryManager()
    test_id = first_entry.get('id')
    
    if not test_id:
        print("   ❌ First entry has no ID!")
        return
    
    print(f"   Testing with ID: {test_id}")
    result = hm.get_entry(test_id)
    
    if result is None:
        print("   ❌ get_entry() returned None!")
        print("   This is the problem - the method can't find the entry")
    else:
        print("   ✓ get_entry() returned data successfully")
        print(f"   - Returned entry has {len(result)} fields")
    
    # Check for common issues
    print("\n5. Checking for common issues...")
    
    # Check if all entries have IDs
    entries_without_id = [e for e in entries if not e.get('id')]
    if entries_without_id:
        print(f"   ⚠️  Found {len(entries_without_id)} entries without IDs")
    else:
        print(f"   ✓ All entries have IDs")
    
    # Check field names that frontend expects
    required_fields = ['id', 'timestamp', 'template_name', 'printer_name', 
                      'quantity', 'status', 'variables']
    missing_fields = {}
    for entry in entries[:5]:  # Check first 5
        entry_id = entry.get('id', 'unknown')
        for field in required_fields:
            if field not in entry:
                if field not in missing_fields:
                    missing_fields[field] = []
                missing_fields[field].append(entry_id)
    
    if missing_fields:
        print(f"   ⚠️  Some entries are missing expected fields:")
        for field, entry_ids in missing_fields.items():
            print(f"     - '{field}' missing in {len(entry_ids)} entries")
    else:
        print(f"   ✓ All checked entries have required fields")
    
    # Check JavaScript expectations
    print("\n6. Checking JavaScript display expectations...")
    print("   The displayJobDetails() function expects:")
    print("     - job.id")
    print("     - job.timestamp")
    print("     - job.template_name")
    print("     - job.printer_name")
    print("     - job.quantity")
    print("     - job.status")
    print("     - job.variables (object)")
    print("     - job.error (optional)")
    
    # Show what the first entry has
    print(f"\n   First entry provides:")
    for field in ['id', 'timestamp', 'template_name', 'printer_name', 
                  'quantity', 'status', 'variables', 'error']:
        if field in first_entry:
            print(f"     ✓ {field}")
        else:
            # Check for alternative field names
            alternatives = {
                'template_name': ['template'],
                'printer_name': ['printer_id'],
            }
            alt_found = False
            if field in alternatives:
                for alt in alternatives[field]:
                    if alt in first_entry:
                        print(f"     ⚠️  {field} (found as '{alt}')")
                        alt_found = True
                        break
            if not alt_found:
                print(f"     ❌ {field} (MISSING)")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    diagnose_history_modal()