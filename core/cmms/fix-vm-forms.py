#!/usr/bin/env python3
"""
Fix VM Forms - Deploy working asset, parts, and work order forms
"""

import requests
import json
import time

def test_vm_apis():
    """Test all the API endpoints on the VM"""
    vm_base = "http://35.237.149.25:8080"
    
    print("🔍 Testing VM API endpoints...")
    
    # Test each API endpoint
    endpoints = [
        "/api/assets",
        "/api/parts", 
        "/api/work-orders",
        "/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{vm_base}{endpoint}", timeout=5)
            print(f"  {endpoint}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"  {endpoint}: ERROR - {str(e)}")
    
    return True

def test_form_functionality():
    """Test if forms can actually create data"""
    vm_base = "http://35.237.149.25:8080"
    
    print("\n🧪 Testing form submission functionality...")
    
    # Test asset creation
    print("Testing asset creation...")
    try:
        asset_data = {
            "name": "Test VM Asset",
            "description": "Testing asset creation on VM",
            "asset_type": "equipment",
            "location": "Test Location",
            "status": "active"
        }
        response = requests.post(f"{vm_base}/api/assets", json=asset_data, timeout=5)
        print(f"  Asset creation: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  Asset creation: ERROR - {str(e)}")
    
    # Test work order creation
    print("Testing work order creation...")
    try:
        wo_data = {
            "title": "Test VM Work Order",
            "description": "Testing work order creation on VM",
            "priority": "medium",
            "status": "open"
        }
        response = requests.post(f"{vm_base}/api/work-orders", json=wo_data, timeout=5)
        print(f"  Work order creation: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  Work order creation: ERROR - {str(e)}")
    
    # Test parts creation
    print("Testing parts creation...")
    try:
        part_data = {
            "name": "Test VM Part",
            "part_number": "TEST-001",
            "description": "Testing part creation on VM",
            "category": "test",
            "quantity": 10,
            "min_stock": 5,
            "unit_cost": 25.99,
            "location": "Test Warehouse"
        }
        response = requests.post(f"{vm_base}/api/parts", json=part_data, timeout=5)
        print(f"  Parts creation: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  Parts creation: ERROR - {str(e)}")

def check_ui_forms():
    """Check if the UI forms exist and have proper functionality"""
    vm_base = "http://35.237.149.25:8080"
    
    print("\n🎨 Checking UI forms...")
    
    pages = [
        ("/assets", "asset form"),
        ("/work-orders", "work order form"), 
        ("/parts", "parts form")
    ]
    
    for page, form_type in pages:
        try:
            response = requests.get(f"{vm_base}{page}", timeout=5)
            content = response.text
            
            # Check for form elements
            has_create_button = "create" in content.lower() or "add" in content.lower()
            has_form_modal = "modal" in content.lower() or "form" in content.lower()
            has_input_fields = "input" in content.lower() and "type=" in content.lower()
            
            print(f"  {form_type}:")
            print(f"    ✅ Create/Add Button: {has_create_button}")
            print(f"    ✅ Form Modal: {has_form_modal}")
            print(f"    ✅ Input Fields: {has_input_fields}")
            
            # Look for specific functionality
            if "alert" in content and "Feature coming soon" in content:
                print(f"    ❌ ISSUE: Form shows 'Feature coming soon' alerts")
            else:
                print(f"    ✅ Form appears functional")
                
        except Exception as e:
            print(f"  {form_type}: ERROR - {str(e)}")

def generate_fix_report():
    """Generate a comprehensive report of what needs to be fixed"""
    print("\n📋 COMPREHENSIVE VM FORMS ANALYSIS")
    print("=" * 50)
    
    test_vm_apis()
    test_form_functionality()
    check_ui_forms()
    
    print("\n🔧 RECOMMENDATIONS:")
    print("1. Deploy working backend_unified_service.py to VM")
    print("2. Replace placeholder forms with functional ones")
    print("3. Ensure API endpoints are properly connected")
    print("4. Test end-to-end form submission flows")

if __name__ == "__main__":
    generate_fix_report()