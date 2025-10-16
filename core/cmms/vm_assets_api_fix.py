# Fix It Fred's Assets API Solution
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
