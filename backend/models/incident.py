from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    incident_type: str = Field(
        ...,
        pattern="^(security_breach|data_leak|system_outage|ai_anomaly|compliance_violation|vendor_issue|performance_degradation|unauthorized_access)$",
    )
    affected_systems: Optional[List[str]] = None
    desc_report_required: Optional[bool] = False


class IncidentUpdate(BaseModel):
    status: Optional[str] = Field(
        None,
        pattern="^(open|investigating|contained|resolved|reported_to_desc)$",
    )
    resolution_notes: Optional[str] = None
    root_cause: Optional[str] = None
    preventive_measures: Optional[str] = None
    assigned_to: Optional[UUID] = None
    desc_report_required: Optional[bool] = None


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    severity: str
    incident_type: str
    status: str
    affected_systems: Optional[List[str]] = None
    reported_by: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    desc_report_required: bool = False
    desc_reported_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolution_date: Optional[datetime] = None
    root_cause: Optional[str] = None
    preventive_measures: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncidentSummary(BaseModel):
    total: int
    open: int
    resolved: int
    reported_to_desc: int
    by_severity: dict
