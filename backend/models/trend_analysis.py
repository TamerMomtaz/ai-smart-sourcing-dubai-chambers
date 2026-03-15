from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date


class TrendAnalysis(BaseModel):
    id: UUID = Field(..., description="Analysis UUID")
    analysis_date: date = Field(..., description="Analysis date")
    sector: Optional[str] = Field(None, description="Sector focus")
    technology_trends: Optional[Dict[str, Any]] = Field(None, description="Technology trends")
    submission_volume: int = Field(..., description="Number of proposals analyzed")
    average_scores: Optional[Dict[str, Any]] = Field(None, description="Average scores")
    emerging_technologies: List[str] = Field(default_factory=list, description="Emerging technologies")
    generated_by: str = Field(..., description="Generator identifier")


class TrendAnalysisGenerateRequest(BaseModel):
    sector: Optional[str] = Field(None, description="Sector to analyze")
    date_range_start: date = Field(..., description="Start date")
    date_range_end: date = Field(..., description="End date")


class TrendAnalysisGenerateResponse(BaseModel):
    job_id: UUID = Field(..., description="Job UUID")
    status: str = Field(default="processing", description="Job status")
    estimated_completion: str = Field(..., description="Estimated completion time")
