#!/usr/bin/env python3
"""Verify the template edit fix works correctly"""

import requests
import json
import sys

# Base URL
BASE_URL = "http://localhost:5000"

def test_template_edit():
    """Test that editing a template with zpl_content field works"""
    
    # Login first
    session = requests.Session()
    login_response = session.post(
        f"{BASE_URL}/login",
        data={"username": "admin", "password": "admin"},
        allow_redirects=False
    )
    
    if login_response.status_code not in [200, 302]:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    print("✅ Login successful")
    
    # Test data with zpl_content field (as sent by frontend)
    template_name = "Shelf_Location.zpl.j2"
    update_data = {
        "name": "Shelf_Location",
        "description": "Chinatown Shelf Location",
        "label_width": 2.3,
        "label_height": 1.2,
        "zpl_content": "^XA\n^FO50,50^A0N,50,50^FDHello World^FS\n^XZ",
        "variables": ["location", "barcode"]
    }
    
    print(f"\n📤 Sending PUT request to /api/templates/{template_name}")
    print(f"   Fields: {list(update_data.keys())}")
    
    response = session.put(
        f"{BASE_URL}/api/templates/{template_name}",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n📥 Response status: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"   Response: {json.dumps(response_data, indent=2)}")
    except:
        print(f"   Response text: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS: Template updated successfully!")
        print("   The fix works - backend now accepts 'zpl_content' field")
        return True
    else:
        print(f"\n❌ FAILED: Status {response.status_code}")
        if response.status_code == 400 and "content" in response.text.lower():
            print("   Issue: Still rejecting zpl_content field")
        elif response.status_code == 422:
            print("   Issue: Validation error (possibly label_size)")
        return False

if __name__ == "__main__":
    success = test_template_edit()
    sys.exit(0 if success else 1)