"""
Vendor Model for ChatterFix CMMS

Represents suppliers and vendors for parts and equipment.
Vendors are organization-scoped for multi-tenant isolation.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timezone


class Vendor(BaseModel):
    """
    Vendor/Supplier model for parts and equipment sourcing.

    Relationships:
    - Referenced by Parts via part.vendor_id (1-to-many)
    - Belongs to Organization via organization_id (many-to-1)
    """
    id: Optional[str] = Field(None, description="Document ID from Firestore")
    organization_id: Optional[str] = Field(None, description="Organization this vendor belongs to")

    # Basic Information
    name: str = Field(..., description="Vendor/company name")
    contact_name: Optional[str] = Field(None, description="Primary contact person")
    email: Optional[str] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")

    # Address Information
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="ZIP/Postal code")
    country: Optional[str] = Field(None, description="Country")

    # Business Information
    website: Optional[str] = Field(None, description="Company website URL")
    account_number: Optional[str] = Field(None, description="Our account number with vendor")
    payment_terms: Optional[str] = Field(None, description="Payment terms (Net 30, etc.)")
    tax_id: Optional[str] = Field(None, description="Tax ID / EIN")

    # Status and Notes
    is_active: bool = Field(True, description="Whether vendor is active")
    is_preferred: bool = Field(False, description="Preferred vendor flag")
    notes: Optional[str] = Field(None, description="Internal notes about vendor")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When vendor was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When vendor was last updated"
    )

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class VendorCreate(BaseModel):
    """Schema for creating a new vendor"""
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    account_number: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    """Schema for updating a vendor"""
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    account_number: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None
    notes: Optional[str] = None
