from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime, timezone


class Asset(BaseModel):
    id: Optional[str] = Field(None, alias="id")
    organization_id: Optional[str] = Field(
        None,
        description="Organization ID for multi-tenant data isolation. "
        "Added at database layer via create_org_document()."
    )
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Maintenance health tracking
    last_maintenance_date: Optional[datetime] = None
    base_health_score: float = Field(default=100.0, ge=0.0, le=100.0)

    @computed_field
    @property
    def maintenance_score(self) -> float:
        """
        AI TEAM CONSENSUS: Calculated dynamically to avoid daily DB writes.
        Decays 1% per day since last maintenance.

        Decision made by:
        - Gemini (Proposer): Suggested cron job
        - Claude (Critic): "Computed on read saves DB writes"
        - Grok (Judge): Approved Claude's approach

        Cost savings: $0/month vs scheduled job costs
        """
        if not self.last_maintenance_date:
            # No maintenance recorded - use base score
            return self.base_health_score

        now = datetime.now(timezone.utc)

        # Handle timezone-naive dates from DB
        last_maint = self.last_maintenance_date
        if last_maint.tzinfo is None:
            last_maint = last_maint.replace(tzinfo=timezone.utc)

        days_since = (now - last_maint).days
        decay_amount = days_since * 1.0  # 1% per day

        return max(0.0, self.base_health_score - decay_amount)

    @property
    def health_status(self) -> str:
        """Human-readable health status based on maintenance score."""
        score = self.maintenance_score
        if score >= 80:
            return "healthy"
        elif score >= 50:
            return "warning"
        elif score >= 20:
            return "critical"
        else:
            return "failing"

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
