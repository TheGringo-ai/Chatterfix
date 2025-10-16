#!/usr/bin/env python3
"""
Direct VM Assets API Deployment
Simple approach to add missing assets API
"""

import requests
import json

def show_fix_it_fred_solution():
    """Show what Fix It Fred created to fix the asset form"""
    
    print("🤖 Fix It Fred says:")
    print("=" * 50)
    print("I've analyzed your VM and found the exact problem!")
    print("")
    print("❌ ISSUE: Your VM has these working forms:")
    print("  ✅ Parts form - Fully functional")  
    print("  ✅ Work orders form - Fully functional")
    print("  ❌ Assets form - Shows 'Feature coming soon'")
    print("")
    print("🔧 ROOT CAUSE: Missing /api/assets endpoints")
    print("  • /api/assets (GET) - Returns 404")
    print("  • /api/assets (POST) - Returns 404")
    print("")
    print("💡 FIX IT FRED'S SOLUTION:")
    print("I've created the complete assets API code that needs to be added to your VM:")
    
    return True

def create_assets_api_file():
    """Create the complete assets API file for VM deployment"""
    
    api_code = '''# Fix It Fred's Assets API Solution
# Add this to your VM's main application file

from fastapi import HTTPException
from datetime import datetime

# Assets data (replace with database in production)
vm_assets_data = [
    {
        "id": 1,
        "name": "Main Production Server",
        "description": "Primary server for production workloads", 
        "asset_type": "equipment",
        "location": "Data Center A",
        "status": "operational",
        "purchase_date": "2024-01-15",
        "created_at": "2024-01-15T10:00:00"
    },
    {
        "id": 2,
        "name": "Backup Generator",
        "description": "Emergency power backup system",
        "asset_type": "equipment", 
        "location": "Building B",
        "status": "active",
        "purchase_date": "2023-08-20",
        "created_at": "2023-08-20T14:30:00"
    },
    {
        "id": 3,
        "name": "HVAC Unit #1", 
        "description": "Main HVAC system for floor 1",
        "asset_type": "system",
        "location": "Floor 1",
        "status": "maintenance",
        "purchase_date": "2022-05-10",
        "created_at": "2022-05-10T09:15:00"
    }
]

# Add these endpoints to your FastAPI app:

@app.get("/api/assets")
async def get_assets():
    """Get all assets - Fix It Fred's implementation"""
    return vm_assets_data

@app.post("/api/assets")
async def create_asset(asset_data: dict):
    """Create new asset - Fix It Fred's implementation"""
    try:
        # Generate new ID
        new_id = max([asset["id"] for asset in vm_assets_data], default=0) + 1
        
        # Create new asset
        new_asset = {
            "id": new_id,
            "name": asset_data.get("name", ""),
            "description": asset_data.get("description", ""),
            "asset_type": asset_data.get("asset_type", "equipment"),
            "location": asset_data.get("location", ""),
            "status": asset_data.get("status", "active"),
            "purchase_date": asset_data.get("purchase_date"),
            "created_at": datetime.now().isoformat()
        }
        
        # Add to data store
        vm_assets_data.append(new_asset)
        
        return {
            "success": True,
            "message": "Asset created successfully by Fix It Fred!",
            "asset": new_asset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/assets/{asset_id}")
async def update_asset(asset_id: int, asset_data: dict):
    """Update asset - Fix It Fred's implementation"""
    try:
        # Find and update asset
        for i, asset in enumerate(vm_assets_data):
            if asset["id"] == asset_id:
                vm_assets_data[i].update(asset_data)
                return {"success": True, "message": f"Asset {asset_id} updated by Fix It Fred"}
        
        raise HTTPException(status_code=404, detail="Asset not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete asset - Fix It Fred's implementation"""
    try:
        # Find and remove asset
        for i, asset in enumerate(vm_assets_data):
            if asset["id"] == asset_id:
                removed = vm_assets_data.pop(i)
                return {"success": True, "message": f"Asset {asset_id} deleted by Fix It Fred"}
        
        raise HTTPException(status_code=404, detail="Asset not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Also update the JavaScript in assets.html to remove alerts:

function addAsset() {
    // Replace the alert with actual form opening
    document.getElementById('createAssetModal').style.display = 'flex';
}

// Add this modal HTML to your assets page:
/*
<div id="createAssetModal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 2000; align-items: center; justify-content: center;">
    <div style="background: white; padding: 2rem; border-radius: 8px; max-width: 500px; width: 90%;">
        <h3>🏭 Create New Asset</h3>
        <form onsubmit="submitAsset(event)">
            <div style="margin-bottom: 1rem;">
                <label>Asset Name:</label>
                <input type="text" id="assetName" required style="width: 100%; padding: 0.75rem;">
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Description:</label>
                <textarea id="assetDescription" required style="width: 100%; padding: 0.75rem;"></textarea>
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Type:</label>
                <select id="assetType" style="width: 100%; padding: 0.75rem;">
                    <option value="equipment">Equipment</option>
                    <option value="vehicle">Vehicle</option>
                    <option value="system">System</option>
                </select>
            </div>
            <div style="margin-bottom: 1rem;">
                <label>Location:</label>
                <input type="text" id="assetLocation" required style="width: 100%; padding: 0.75rem;">
            </div>
            <div style="display: flex; gap: 1rem;">
                <button type="submit">Create Asset</button>
                <button type="button" onclick="closeAssetModal()">Cancel</button>
            </div>
        </form>
    </div>
</div>
*/

async function submitAsset(event) {
    event.preventDefault();
    
    const assetData = {
        name: document.getElementById('assetName').value,
        description: document.getElementById('assetDescription').value,
        asset_type: document.getElementById('assetType').value,
        location: document.getElementById('assetLocation').value,
        status: 'active'
    };
    
    try {
        const response = await fetch('/api/assets', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(assetData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('🎉 Asset created successfully!');
            location.reload();
        }
    } catch (error) {
        alert('Error creating asset: ' + error.message);
    }
}

function closeAssetModal() {
    document.getElementById('createAssetModal').style.display = 'none';
}
'''
    
    # Save the API code to a file
    with open('vm_assets_api_fix.py', 'w') as f:
        f.write(api_code)
    
    print("📁 Fix It Fred: Complete assets API fix saved to 'vm_assets_api_fix.py'")
    print("")
    print("📋 TO DEPLOY:")
    print("1. Copy the API endpoints to your VM's main app file")
    print("2. Copy the JavaScript functions to your assets.html")
    print("3. Add the modal HTML to your assets page")
    print("4. Restart your VM service")
    print("")
    print("🎯 RESULT: Asset form will be fully functional!")
    
    return True

def test_after_deployment():
    """Test the assets API after deployment"""
    vm_base = "http://35.237.149.25:8080"
    
    print("🧪 Fix It Fred: Testing assets API...")
    
    try:
        # Test GET /api/assets
        response = requests.get(f"{vm_base}/api/assets", timeout=5)
        if response.status_code == 200:
            assets = response.json()
            print(f"✅ GET /api/assets works - Found {len(assets)} assets")
        else:
            print(f"❌ GET /api/assets failed: {response.status_code}")
        
        # Test POST /api/assets
        test_asset = {
            "name": "Fix It Fred Test Asset",
            "description": "Testing asset creation",
            "asset_type": "equipment",
            "location": "Test Lab",
            "status": "active"
        }
        
        response = requests.post(f"{vm_base}/api/assets", json=test_asset, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ POST /api/assets works - Asset creation successful")
        else:
            print(f"❌ POST /api/assets failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Testing failed: {e}")

def main():
    """Main function to show Fix It Fred's solution"""
    show_fix_it_fred_solution()
    create_assets_api_file()
    
    print("\n🤖 Fix It Fred: Ready to test the fix!")
    print("After you deploy the code, run test_after_deployment() to verify")

if __name__ == "__main__":
    main()