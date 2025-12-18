from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Part(BaseModel):
    id: Optional[str] = Field(None, alias="id")
    name: str
    part_number: str
    category: str
    description: Optional[str] = None
    current_stock: int = 0
    minimum_stock: int = 0
    unit_cost: float = 0.0
    location: Optional[str] = None
    supplier: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
