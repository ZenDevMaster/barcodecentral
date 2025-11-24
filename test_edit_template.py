#!/usr/bin/env python3
"""Test script to reproduce the template edit error"""

import requests
import json

# Base URL
BASE_URL = "http://localhost:5000"

# Login first
session = requests.Session()
login_response = session.post(
    f"{BASE_URL}/login",
    data={
        "username": "admin",
        "password": "admin"
    },
    allow_redirects=False
)

print(f"Login status: {login_response.status_code}")

# Now try to update the template
template_name = "Shelf_Location.zpl.j2"
update_data = {
    "name": "Shelf_Location",
    "description": "Chinatown Shelf Location",
    "label_width": 2.3,
    "label_height": 1.2,
    "zpl_content": "^XA\n^FO50,50^A0N,50,50^FDHello World^FS\n^XZ",
    "variables": ["location", "barcode"]
}

print(f"\nSending PUT request to /api/templates/{template_name}")
print(f"Request data: {json.dumps(update_data, indent=2)}")

response = session.put(
    f"{BASE_URL}/api/templates/{template_name}",
    json=update_data,
    headers={"Content-Type": "application/json"}
)

print(f"\nResponse status: {response.status_code}")
print(f"Response body: {response.text}")

# Check logs
print("\n" + "="*60)
print("Checking application logs...")
print("="*60)
import subprocess
result = subprocess.run(["tail", "-20", "/tmp/app_debug.log"], capture_output=True, text=True)
print(result.stdout)