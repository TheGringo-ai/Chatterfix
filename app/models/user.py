from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class Organization(BaseModel):
    """
    Pydantic model for an organization/company.
    Each company has its own isolated data in Firestore.
    """

    id: str
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    created_at: Optional[str] = None


class User(BaseModel):
    """
    Pydantic model for a user, designed to work with Firebase Authentication.
    Multi-tenant support: Each user belongs to an organization.
    """

    uid: str
    email: EmailStr
    role: str = "technician"
    full_name: Optional[str] = None
    disabled: bool = False
    permissions: List[str] = []
    # Multi-tenant fields
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    company: Optional[Dict[str, Any]] = None


class TokenData(BaseModel):
    """
    Pydantic model for the data encoded in a JWT.
    """

    uid: str
    email: EmailStr
    organization_id: Optional[str] = None
