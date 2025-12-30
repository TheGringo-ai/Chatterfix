#!/usr/bin/env python3
"""
Parts Management Module
Easily editable parts inventory system
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/parts", tags=["Parts"])

# Parts Models
class Part(BaseModel):
    id: str
    name: str
    description: str
    quantity: int
    price: float
    supplier: str
    location: str
    last_updated: datetime

class PartCreate(BaseModel):
    name: str
    description: str
    quantity: int
    price: float
    supplier: str
    location: str

# In-memory parts database (easily replaceable with real DB)
parts_db = {}

@router.get("/", response_model=List[Part])
async def get_all_parts():
    """Get all parts in inventory"""
    return list(parts_db.values())

@router.get("/{part_id}", response_model=Part)
async def get_part(part_id: str):
    """Get specific part by ID"""
    if part_id not in parts_db:
        raise HTTPException(status_code=404, detail="Part not found")
    return parts_db[part_id]

@router.post("/", response_model=Part)
async def create_part(part: PartCreate):
    """Create new part"""
    part_id = f"PART_{len(parts_db) + 1:04d}"
    new_part = Part(
        id=part_id,
        **part.dict(),
        last_updated=datetime.now()
    )
    parts_db[part_id] = new_part
    return new_part

@router.put("/{part_id}", response_model=Part)
async def update_part(part_id: str, part: PartCreate):
    """Update existing part"""
    if part_id not in parts_db:
        raise HTTPException(status_code=404, detail="Part not found")
    
    updated_part = Part(
        id=part_id,
        **part.dict(),
        last_updated=datetime.now()
    )
    parts_db[part_id] = updated_part
    return updated_part

@router.delete("/{part_id}")
async def delete_part(part_id: str):
    """Delete part"""
    if part_id not in parts_db:
        raise HTTPException(status_code=404, detail="Part not found")
    
    del parts_db[part_id]
    return {"message": "Part deleted successfully"}

@router.get("/search/{query}")
async def search_parts(query: str):
    """Search parts by name or description"""
    results = []
    for part in parts_db.values():
        if query.lower() in part.name.lower() or query.lower() in part.description.lower():
            results.append(part)
    return results