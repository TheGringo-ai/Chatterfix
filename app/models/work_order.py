from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WorkOrder(BaseModel):
    id: Optional[str] = Field(None, alias='id')
    title: str
    description: str
    priority: str
    status: str
    assigned_to_uid: Optional[str] = None
    assigned_to_name: Optional[str] = None
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    work_order_type: str
    created_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    work_summary: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
