from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime


class EvaluationWeightConfig(BaseModel):
    relevance_weight: float = Field(..., ge=0, le=1, description="Relevance weight (0-1)")
    feasibility_weight: float = Field(..., ge=0, le=1, description="Feasibility weight (0-1)")
    sector_alignment_weight: float = Field(..., ge=0, le=1, description="Sector alignment weight (0-1)")
    compliance_weight: float = Field(..., ge=0, le=1, description="Compliance weight (0-1)")

    @field_validator("relevance_weight", "feasibility_weight", "sector_alignment_weight", "compliance_weight")
    @classmethod
    def validate_sum(cls, v, info):
        return v


class BusinessGroup(BaseModel):
    id: UUID = Field(..., description="Business group UUID")
    name: str = Field(..., description="Business group name")
    chamber: str = Field(..., description="Parent chamber name")
    description: Optional[str] = Field(None, description="Group description")
    sector_kpis: Optional[Dict[str, Any]] = Field(None, description="Sector-specific KPIs")
    lead_user_id: Optional[UUID] = Field(None, description="Group lead user ID")
    lead_name: Optional[str] = Field(None, description="Group lead name")


class BusinessGroupDetail(BaseModel):
    id: UUID = Field(..., description="Business group UUID")
    name: str = Field(..., description="Business group name")
    chamber: str = Field(..., description="Parent chamber name")
    description: Optional[str] = Field(None, description="Group description")
    sector_kpis: Optional[Dict[str, Any]] = Field(None, description="Sector-specific KPIs")
    evaluation_weight_config: Optional[Dict[str, Any]] = Field(None, description="Evaluation weight configuration")
    lead_user_id: Optional[UUID] = Field(None, description="Group lead user ID")
    lead_name: Optional[str] = Field(None, description="Group lead name")
    proposal_count: int = Field(..., description="Number of proposals")
    average_composite_score: Optional[float] = Field(None, description="Average composite score")


class EvaluationWeightConfigUpdate(BaseModel):
    evaluation_weight_config: EvaluationWeightConfig = Field(..., description="Updated evaluation weights")


class EvaluationWeightConfigUpdateResponse(BaseModel):
    business_group_id: UUID = Field(..., description="Business group UUID")
    evaluation_weight_config: Dict[str, Any] = Field(..., description="Updated evaluation weights")
    updated_at: datetime = Field(..., description="Update timestamp")
