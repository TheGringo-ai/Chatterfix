"""
Part/Inventory Model for ChatterFix CMMS

Represents parts and inventory items used in maintenance operations.
Parts are organization-scoped for multi-tenant isolation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class Part(BaseModel):
    """
    Part/Inventory item model.

    Relationships:
    - Referenced by WorkOrders via work_order.parts_used array (many-to-many)
    - Links to Vendor via vendor_id (many-to-1)
    - Belongs to Organization via organization_id (many-to-1)
    - Can be linked to Assets via asset_parts collection (many-to-many)
    """
    id: Optional[str] = Field(None, description="Document ID from Firestore")
    organization_id: Optional[str] = Field(None, description="Organization this part belongs to")

    # Basic Information
    name: str = Field(..., description="Part name")
    part_number: str = Field(..., description="Manufacturer part number")
    category: str = Field(..., description="Category (Bearings, Seals, Filters, etc.)")
    description: Optional[str] = Field(None, description="Detailed description")

    # Inventory Tracking
    current_stock: int = Field(0, description="Current quantity in stock")
    minimum_stock: int = Field(5, description="Reorder point - alert when below this")
    maximum_stock: Optional[int] = Field(None, description="Maximum stock level")
    unit_of_measure: str = Field("each", description="Unit of measure (each, box, case, etc.)")

    # Cost Information
    unit_cost: float = Field(0.0, description="Cost per unit")
    last_purchase_cost: Optional[float] = Field(None, description="Cost from last purchase")
    last_purchase_date: Optional[datetime] = Field(None, description="Date of last purchase")

    # Location and Storage
    location: Optional[str] = Field(None, description="Warehouse bin/location")
    warehouse: Optional[str] = Field(None, description="Warehouse name")
    aisle: Optional[str] = Field(None, description="Aisle location")
    shelf: Optional[str] = Field(None, description="Shelf location")

    # Vendor/Supplier Information
    vendor_id: Optional[str] = Field(None, description="FK to vendors collection")
    supplier: Optional[str] = Field(None, description="Supplier name (legacy/denormalized)")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    manufacturer_part_number: Optional[str] = Field(None, description="OEM part number")

    # Media
    image_url: Optional[str] = Field(None, description="Part image URL")
    barcode: Optional[str] = Field(None, description="Barcode for scanning")

    # Status
    is_active: bool = Field(True, description="Whether part is active/orderable")
    is_critical: bool = Field(False, description="Critical spare part flag")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When part was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When part was last updated"
    )

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
