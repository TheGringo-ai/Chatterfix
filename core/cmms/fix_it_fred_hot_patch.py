#!/usr/bin/env python3
"""
Fix It Fred Hot Patch - Direct VM Integration
Actually add the assets API to the running VM service
"""

import requests
import json

def fix_it_fred_hot_patch():
    """Fix It Fred's direct integration approach"""
    
    print("🤖 Fix It Fred: REAL Problem Identified!")
    print("=" * 60)
    print("❌ ISSUE: My code is in GitHub but NOT running on the VM")
    print("✅ SOLUTION: Hot-patch the running VM service directly")
    print()
    
    vm_base = "http://35.237.149.25:8080"
    
    print("🔧 Fix It Fred's Hot Patch Strategy:")
    print("1. The VM is running ChatterFix v4.0.0 with placeholder assets")
    print("2. I need to REPLACE the placeholder with my working code") 
    print("3. Use the VM's live update mechanism")
    print()
    
    # Check what the VM actually supports for live updates
    print("🔍 Checking VM's live update capabilities...")
    
    # Look for admin/management endpoints
    endpoints_to_check = [
        "/admin/reload",
        "/api/admin/update", 
        "/management/hot-deploy",
        "/api/management/reload-modules",
        "/dev/hot-reload",
        "/api/system/reload"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f"{vm_base}{endpoint}", timeout=3)
            if response.status_code == 200:
                print(f"✅ Found management endpoint: {endpoint}")
            elif response.status_code == 404:
                print(f"❌ No endpoint: {endpoint}")
            else:
                print(f"⚠️  Endpoint {endpoint}: Status {response.status_code}")
        except:
            print(f"❌ Cannot reach: {endpoint}")
    
    print()
    print("🎯 Fix It Fred's Direct Approach:")
    print("Since the VM doesn't have hot-reload endpoints, I need to:")
    print("1. Find the VM's source code location")
    print("2. Directly update the running service files")
    print("3. Restart the service")
    
    return True

def create_vm_update_script():
    """Create a script to update the VM directly"""
    
    update_script = '''#!/bin/bash
# Fix It Fred VM Update Script
# Directly update the running ChatterFix service

echo "🤖 Fix It Fred: Updating VM assets API..."

VM_IP="35.237.149.25"
VM_USER="fredtaylor"  # Replace with actual VM user

# The working assets API code that needs to be added
cat > assets_api_patch.py << 'EOF'
# Fix It Fred's Working Assets API
from fastapi import HTTPException
from datetime import datetime
import uuid

# Assets data store
vm_assets = [
    {"id": str(uuid.uuid4()), "name": "Server #1", "type": "equipment", "location": "DC-A", "status": "active"},
    {"id": str(uuid.uuid4()), "name": "Generator", "type": "equipment", "location": "Building B", "status": "operational"},
    {"id": str(uuid.uuid4()), "name": "HVAC #1", "type": "system", "location": "Floor 1", "status": "maintenance"}
]

@app.get("/api/assets")
async def get_assets():
    return vm_assets

@app.post("/api/assets") 
async def create_asset(asset_data: dict):
    new_asset = {
        "id": str(uuid.uuid4()),
        "name": asset_data.get("name", ""),
        "description": asset_data.get("description", ""),
        "asset_type": asset_data.get("asset_type", "equipment"),
        "location": asset_data.get("location", ""),
        "status": asset_data.get("status", "active"),
        "created_at": datetime.now().isoformat()
    }
    vm_assets.append(new_asset)
    return {"success": True, "message": "Asset created by Fix It Fred", "asset": new_asset}
EOF

echo "📦 Assets API patch created"

# Now we need to integrate this into the running service
echo "🔧 Next steps:"
echo "1. SSH into VM: ssh $VM_USER@$VM_IP"
echo "2. Find the ChatterFix service files"
echo "3. Add the assets API endpoints"
echo "4. Restart the service"

echo "🎯 Fix It Fred: Manual integration required for VM access"
'''
    
    with open('vm_update_script.sh', 'w') as f:
        f.write(update_script)
    
    print("📄 Fix It Fred: VM update script created")
    return True

def test_current_vm_state():
    """Test what's actually on the VM right now"""
    
    print("🧪 Fix It Fred: Testing current VM state...")
    vm_base = "http://35.237.149.25:8080"
    
    # Test the problematic assets API
    try:
        response = requests.get(f"{vm_base}/api/assets", timeout=5)
        print(f"GET /api/assets: {response.status_code}")
        if response.status_code == 404:
            print("❌ CONFIRMED: Assets API missing from VM")
        elif response.status_code == 200:
            print("✅ Assets API exists - checking if functional")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    # Check if we can create an asset
    try:
        test_asset = {"name": "Fix It Fred Test", "asset_type": "equipment", "location": "Test"}
        response = requests.post(f"{vm_base}/api/assets", json=test_asset, timeout=5)
        print(f"POST /api/assets: {response.status_code}")
        if response.status_code == 404:
            print("❌ CONFIRMED: Cannot create assets - endpoint missing")
        elif response.status_code == 200:
            print("✅ Asset creation works")
    except Exception as e:
        print(f"❌ Asset creation test failed: {e}")
    
    # Check the asset form JavaScript
    try:
        response = requests.get(f"{vm_base}/assets", timeout=5)
        if "Feature coming soon" in response.text:
            print("❌ CONFIRMED: Asset form still shows placeholder")
        else:
            print("⚠️  Asset form may have been updated")
    except Exception as e:
        print(f"❌ Asset form check failed: {e}")

def main():
    """Fix It Fred's main troubleshooting function"""
    print("🤖 Fix It Fred: VM Integration Troubleshooting")
    print("=" * 60)
    
    fix_it_fred_hot_patch()
    test_current_vm_state()
    create_vm_update_script()
    
    print()
    print("🎯 Fix It Fred's Diagnosis:")
    print("The GitHub deployment did NOT update the running VM service.")
    print("The VM needs direct file updates or service restart.")
    print()
    print("💡 SOLUTIONS:")
    print("1. SSH into VM and manually add assets API")
    print("2. Use VM management interface to reload code")
    print("3. Restart the ChatterFix service on VM")
    print("4. Deploy via VM's continuous deployment pipeline")
    print()
    print("🚀 Ready for manual VM integration!")

if __name__ == "__main__":
    main()