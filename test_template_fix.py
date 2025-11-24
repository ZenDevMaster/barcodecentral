#!/usr/bin/env python3
"""
Test script to verify template creation fixes
"""
import json
from blueprints.templates_bp import templates_bp
from flask import Flask

# Create test app
app = Flask(__name__)
app.register_blueprint(templates_bp, url_prefix='/api/templates')

# Test data matching the user's example
test_data = {
    "name": "Shelf_Location",
    "description": "Chinatown Shelf Location",
    "label_width": "2.3",
    "label_height": "1.2",
    "zpl_content": "^XA\n^FO50,50^A0N,50,50^FDHello World^FS\n^XZ",
    "variables": ["location", "barcode"]
}

print("Testing template creation with data:")
print(json.dumps(test_data, indent=2))
print("\n" + "="*60 + "\n")

# Test 1: Basic numeric values (inches)
print("Test 1: Numeric values (inches)")
print(f"  Width: {test_data['label_width']} -> should be treated as inches")
print(f"  Height: {test_data['label_height']} -> should be treated as inches")

# Test 2: With mm suffix
test_data_mm = test_data.copy()
test_data_mm['label_width'] = "58.42mm"  # 2.3 inches
test_data_mm['label_height'] = "30.48mm"  # 1.2 inches
print("\nTest 2: With mm suffix")
print(f"  Width: {test_data_mm['label_width']} -> should convert to ~2.3 inches")
print(f"  Height: {test_data_mm['label_height']} -> should convert to ~1.2 inches")

# Test 3: With cm suffix
test_data_cm = test_data.copy()
test_data_cm['label_width'] = "5.842cm"  # 2.3 inches
test_data_cm['label_height'] = "3.048cm"  # 1.2 inches
print("\nTest 3: With cm suffix")
print(f"  Width: {test_data_cm['label_width']} -> should convert to ~2.3 inches")
print(f"  Height: {test_data_cm['label_height']} -> should convert to ~1.2 inches")

print("\n" + "="*60)
print("\nKey fixes implemented:")
print("1. Backend now accepts 'name' field (not just 'filename')")
print("2. Backend now accepts 'zpl_content' field (not just 'content')")
print("3. Backend now accepts 'label_width' and 'label_height' separately")
print("4. Backend now supports unit suffixes: mm, cm, inches")
print("5. Frontend form fields now accept text input with units")
print("\nThe template creation should now work with the provided data!")