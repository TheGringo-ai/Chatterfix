#!/bin/bash
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
