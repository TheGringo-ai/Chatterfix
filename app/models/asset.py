from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Asset(BaseModel):
    id: Optional[str] = Field(None, alias="id")
    name: str
    description: Optional[str] = None
    asset_tag: Optional[str] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    parent_asset_id: Optional[str] = None
    status: str = "Active"
    criticality: str = "Medium"
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    purchase_cost: Optional[float] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
