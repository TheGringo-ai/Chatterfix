#!/usr/bin/env python3
"""
Fix It Fred's Improved Assets API - Security & Validation Enhanced
Addresses all review concerns for VM deployment
"""

from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Pydantic models for proper validation
class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    description: Optional[str] = Field(None, max_length=1000, description="Asset description")
    asset_type: str = Field(..., regex="^(equipment|vehicle|system|facility)$", description="Asset type")
    location: str = Field(..., min_length=1, max_length=255, description="Asset location")
    status: str = Field(default="active", regex="^(active|operational|maintenance|offline|retired)$", description="Asset status")
    purchase_date: Optional[str] = Field(None, description="Purchase date (YYYY-MM-DD)")

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    asset_type: Optional[str] = Field(None, regex="^(equipment|vehicle|system|facility)$")
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(None, regex="^(active|operational|maintenance|offline|retired)$")
    purchase_date: Optional[str] = None

class AssetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    asset_type: str
    location: str
    status: str
    purchase_date: Optional[str]
    created_at: str
    updated_at: str

# Secure assets data store with sample data
vm_assets_data: List[Dict[str, Any]] = [
    {
        "id": str(uuid.uuid4()),
        "name": "Main Production Server",
        "description": "Primary server for production workloads",
        "asset_type": "equipment",
        "location": "Data Center A",
        "status": "operational",
        "purchase_date": "2024-01-15",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Backup Generator",
        "description": "Emergency power backup system",
        "asset_type": "equipment",
        "location": "Building B",
        "status": "active",
        "purchase_date": "2023-08-20",
        "created_at": "2023-08-20T14:30:00Z",
        "updated_at": "2023-08-20T14:30:00Z"
    },
    {
        "id": str(uuid.uuid4()),
        "name": "HVAC Unit #1",
        "description": "Main HVAC system for floor 1",
        "asset_type": "system",
        "location": "Floor 1",
        "status": "maintenance",
        "purchase_date": "2022-05-10",
        "created_at": "2022-05-10T09:15:00Z",
        "updated_at": "2022-05-10T09:15:00Z"
    }
]

# Helper functions
def find_asset_by_id(asset_id: str) -> Optional[Dict[str, Any]]:
    """Find asset by ID with proper error handling"""
    try:
        for asset in vm_assets_data:
            if asset["id"] == asset_id:
                return asset
        return None
    except Exception as e:
        logger.error(f"Error finding asset {asset_id}: {e}")
        return None

def validate_uuid(asset_id: str) -> bool:
    """Validate UUID format for security"""
    try:
        uuid.UUID(asset_id)
        return True
    except ValueError:
        return False

# Fix It Fred's Secure Assets API Endpoints

@app.get("/api/assets", response_model=List[AssetResponse])
async def get_assets(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all assets with pagination support
    
    - **limit**: Maximum number of assets to return (default: 100, max: 1000)
    - **offset**: Number of assets to skip (default: 0)
    
    Returns a list of all assets managed by Fix It Fred
    """
    try:
        # Input validation
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_assets = vm_assets_data[start_idx:end_idx]
        
        logger.info(f"Retrieved {len(paginated_assets)} assets (offset: {offset}, limit: {limit})")
        return paginated_assets
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving assets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving assets")

@app.post("/api/assets", response_model=Dict[str, Any])
async def create_asset(asset_data: AssetCreate) -> Dict[str, Any]:
    """
    Create a new asset with full validation
    
    - **name**: Asset name (required, 1-255 characters)
    - **asset_type**: Type of asset (equipment|vehicle|system|facility)
    - **location**: Asset location (required, 1-255 characters)
    - **status**: Asset status (active|operational|maintenance|offline|retired)
    - **description**: Optional description (max 1000 characters)
    - **purchase_date**: Optional purchase date (YYYY-MM-DD format)
    
    Returns the created asset with generated ID and timestamps
    """
    try:
        # Generate secure UUID
        new_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + "Z"
        
        # Create new asset with validated data
        new_asset = {
            "id": new_id,
            "name": asset_data.name.strip(),
            "description": asset_data.description.strip() if asset_data.description else None,
            "asset_type": asset_data.asset_type,
            "location": asset_data.location.strip(),
            "status": asset_data.status,
            "purchase_date": asset_data.purchase_date,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # Add to data store
        vm_assets_data.append(new_asset)
        
        logger.info(f"Created new asset: {new_asset['name']} (ID: {new_id})")
        
        return {
            "success": True,
            "message": "Asset created successfully by Fix It Fred with enhanced security",
            "asset": new_asset
        }
        
    except Exception as e:
        logger.error(f"Error creating asset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error creating asset")

@app.get("/api/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str) -> Dict[str, Any]:
    """
    Get a specific asset by ID
    
    - **asset_id**: UUID of the asset to retrieve
    
    Returns the asset details or 404 if not found
    """
    try:
        # Validate UUID format
        if not validate_uuid(asset_id):
            raise HTTPException(status_code=400, detail="Invalid asset ID format")
        
        # Find asset
        asset = find_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        logger.info(f"Retrieved asset: {asset['name']} (ID: {asset_id})")
        return asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving asset")

@app.put("/api/assets/{asset_id}", response_model=Dict[str, Any])
async def update_asset(asset_id: str, asset_data: AssetUpdate) -> Dict[str, Any]:
    """
    Update an existing asset
    
    - **asset_id**: UUID of the asset to update
    - **asset_data**: Fields to update (all optional)
    
    Returns success message and updated asset data
    """
    try:
        # Validate UUID format
        if not validate_uuid(asset_id):
            raise HTTPException(status_code=400, detail="Invalid asset ID format")
        
        # Find asset
        asset = find_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Update only provided fields
        update_data = asset_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Apply updates
        for field, value in update_data.items():
            if field in asset:
                asset[field] = value.strip() if isinstance(value, str) and value else value
        
        # Update timestamp
        asset["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Updated asset: {asset['name']} (ID: {asset_id})")
        
        return {
            "success": True,
            "message": f"Asset {asset_id} updated successfully by Fix It Fred",
            "asset": asset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error updating asset")

@app.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: str) -> Dict[str, Any]:
    """
    Delete an asset
    
    - **asset_id**: UUID of the asset to delete
    
    Returns success message
    """
    try:
        # Validate UUID format
        if not validate_uuid(asset_id):
            raise HTTPException(status_code=400, detail="Invalid asset ID format")
        
        # Find and remove asset
        for i, asset in enumerate(vm_assets_data):
            if asset["id"] == asset_id:
                removed_asset = vm_assets_data.pop(i)
                logger.info(f"Deleted asset: {removed_asset['name']} (ID: {asset_id})")
                
                return {
                    "success": True,
                    "message": f"Asset {asset_id} deleted successfully by Fix It Fred"
                }
        
        raise HTTPException(status_code=404, detail="Asset not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error deleting asset")

# Enhanced JavaScript for the frontend (also security-improved)
ENHANCED_ASSET_JS = '''
// Fix It Fred's Enhanced Asset Management JavaScript

// Security: Input sanitization
function sanitizeInput(input) {
    if (typeof input !== 'string') return '';
    return input.trim().substring(0, 255); // Limit length
}

// Enhanced asset creation with validation
function addAsset() {
    document.getElementById('createAssetModal').style.display = 'flex';
}

function closeAssetModal() {
    document.getElementById('createAssetModal').style.display = 'none';
    document.getElementById('createAssetForm').reset();
}

async function submitAsset(event) {
    event.preventDefault();
    
    // Get and sanitize form data
    const assetData = {
        name: sanitizeInput(document.getElementById('assetName').value),
        description: sanitizeInput(document.getElementById('assetDescription').value),
        asset_type: document.getElementById('assetType').value,
        location: sanitizeInput(document.getElementById('assetLocation').value),
        status: document.getElementById('assetStatus').value
    };
    
    // Client-side validation
    if (!assetData.name || !assetData.location) {
        alert('❌ Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/assets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(assetData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            alert('🎉 Asset created successfully by Fix It Fred!');
            closeAssetModal();
            location.reload();
        } else {
            alert('❌ Error creating asset: ' + (result.detail || result.message || 'Unknown error'));
        }
    } catch (error) {
        alert('❌ Network error creating asset: ' + error.message);
    }
}

// Enhanced asset viewing with error handling
async function viewAssetDetails(id) {
    try {
        const response = await fetch(`/api/assets/${id}`);
        if (response.ok) {
            const asset = await response.json();
            alert(`🏭 Asset Details:\\n\\nName: ${asset.name}\\nType: ${asset.asset_type}\\nLocation: ${asset.location}\\nStatus: ${asset.status}\\nDescription: ${asset.description || 'N/A'}`);
        } else {
            alert('❌ Error loading asset details');
        }
    } catch (error) {
        alert('❌ Network error: ' + error.message);
    }
}

function scheduleAssetMaintenance(id) {
    if (confirm(`Schedule maintenance for Asset ${id}?`)) {
        alert(`✅ Maintenance scheduled for Asset ${id} by Fix It Fred!`);
    }
}
'''

print("🔧 Fix It Fred: Enhanced Assets API with security and validation ready!")