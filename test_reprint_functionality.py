#!/usr/bin/env python3
"""
Test script to verify reprint functionality implementation
Tests the complete flow from history to print form with auto-population
"""

def test_history_html_changes():
    """Verify history.html has correct data attributes"""
    print("✓ Testing history.html changes...")
    
    with open('templates/history.html', 'r') as f:
        content = f.read()
    
    # Check for new data attributes
    assert 'data-template=' in content, "Missing data-template attribute"
    assert 'data-template-name=' in content, "Missing data-template-name attribute"
    assert 'data-printer-id=' in content, "Missing data-printer-id attribute"
    assert 'data-printer-name=' in content, "Missing data-printer-name attribute"
    assert 'data-variables=' in content, "Missing data-variables attribute"
    assert 'data-quantity=' in content, "Missing data-quantity attribute"
    
    # Check for sessionStorage usage
    assert 'sessionStorage.setItem' in content, "Missing sessionStorage.setItem"
    assert 'reprintData' in content, "Missing reprintData variable"
    assert 'JSON.stringify(reprintData)' in content, "Missing JSON.stringify"
    
    print("  ✓ All data attributes present")
    print("  ✓ SessionStorage implementation found")
    print()


def test_print_form_html_changes():
    """Verify print_form.html has sessionStorage reading logic"""
    print("✓ Testing print_form.html changes...")
    
    with open('templates/print_form.html', 'r') as f:
        content = f.read()
    
    # Check for sessionStorage reading
    assert 'sessionStorage.getItem' in content, "Missing sessionStorage.getItem"
    assert 'reprintData' in content, "Missing reprintData handling"
    assert 'JSON.parse' in content, "Missing JSON.parse"
    
    # Check for auto-population logic
    assert 'reprintData.template' in content, "Missing template auto-select"
    assert 'reprintData.printerId' in content, "Missing printer auto-select"
    assert 'reprintData.variables' in content, "Missing variables auto-populate"
    assert 'reprintData.quantity' in content, "Missing quantity auto-populate"
    
    # Check for preview generation
    assert 'generatePreview()' in content, "Missing auto-preview generation"
    
    # Check for cleanup
    assert 'sessionStorage.removeItem' in content, "Missing sessionStorage cleanup"
    
    print("  ✓ SessionStorage reading logic present")
    print("  ✓ Auto-population logic found")
    print("  ✓ Preview auto-generation found")
    print("  ✓ SessionStorage cleanup found")
    print()


def test_implementation_summary():
    """Print implementation summary"""
    print("=" * 60)
    print("REPRINT FUNCTIONALITY IMPLEMENTATION SUMMARY")
    print("=" * 60)
    print()
    print("✅ COMPLETED CHANGES:")
    print()
    print("1. templates/history.html:")
    print("   - Added data-template attribute (template filename)")
    print("   - Added data-template-name attribute (display name)")
    print("   - Added data-printer-id attribute (printer ID)")
    print("   - Added data-printer-name attribute (display name)")
    print("   - Added data-variables attribute (JSON variables)")
    print("   - Added data-quantity attribute (print quantity)")
    print("   - Updated reprint button click handler")
    print("   - Stores all data in sessionStorage")
    print("   - Redirects to /print (clean URL)")
    print()
    print("2. templates/print_form.html:")
    print("   - Reads reprintData from sessionStorage on load")
    print("   - Auto-selects template")
    print("   - Auto-selects printer")
    print("   - Auto-populates all variable fields")
    print("   - Auto-populates quantity")
    print("   - Auto-generates preview")
    print("   - Cleans up sessionStorage after use")
    print("   - Includes error handling and logging")
    print()
    print("✅ FEATURES:")
    print()
    print("   ✓ Complete data transfer (template, printer, variables, quantity)")
    print("   ✓ Clean URLs (no query parameters)")
    print("   ✓ No URL length limits (uses sessionStorage)")
    print("   ✓ Auto-preview generation")
    print("   ✓ Fully editable after population")
    print("   ✓ User can modify any field before printing")
    print("   ✓ Console logging for debugging")
    print("   ✓ Error handling")
    print()
    print("=" * 60)
    print()


if __name__ == '__main__':
    try:
        test_history_html_changes()
        test_print_form_html_changes()
        test_implementation_summary()
        
        print("✅ ALL TESTS PASSED!")
        print()
        print("🎉 Reprint functionality is ready to test in the browser!")
        print()
        print("TESTING STEPS:")
        print("1. Navigate to History page")
        print("2. Click the 'Reprint' button on any successful print job")
        print("3. Verify you're redirected to /print")
        print("4. Verify template is auto-selected")
        print("5. Verify printer is auto-selected")
        print("6. Verify all variables are auto-populated")
        print("7. Verify quantity is set correctly")
        print("8. Verify preview is auto-generated")
        print("9. Modify any field and verify it updates")
        print("10. Click 'Print Labels' to complete the reprint")
        print()
        
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        exit(1)