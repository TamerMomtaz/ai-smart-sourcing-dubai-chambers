from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class BatchEvaluateRequest(BaseModel):
    proposal_ids: List[UUID] = Field(..., max_length=100, description="Proposal UUIDs to evaluate")


class BatchJobResponse(BaseModel):
    batch_job_id: UUID = Field(..., description="Batch job UUID")
    proposal_count: int = Field(..., description="Number of proposals in batch")
    status: str = Field(default="queued", description="Batch job status")
    estimated_completion: datetime = Field(..., description="Estimated completion timestamp")


class BatchJobStatus(BaseModel):
    batch_job_id: UUID = Field(..., description="Batch job UUID")
    status: Literal["queued", "processing", "completed", "failed"] = Field(..., description="Batch job status")
    total_proposals: int = Field(..., description="Total proposals in batch")
    processed: int = Field(..., description="Number of processed proposals")
    failed: int = Field(..., description="Number of failed proposals")
    started_at: datetime = Field(..., description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
