from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class AIInteractionInfo(BaseModel):
    model_name: str = Field(..., description="AI model name")
    prompt_tokens: int = Field(..., description="Prompt tokens")
    completion_tokens: int = Field(..., description="Completion tokens")
    latency_ms: int = Field(..., description="Response latency in ms")
    cost_usd: float = Field(..., description="Cost in USD")
    operation_type: str = Field(..., description="Operation type")


class EvaluationResponse(BaseModel):
    id: UUID = Field(..., description="Evaluation UUID")
    proposal_id: UUID = Field(..., description="Proposal UUID")
    relevance_score: float = Field(..., description="Relevance score")
    feasibility_score: float = Field(..., description="Feasibility score")
    sector_alignment_score: float = Field(..., description="Sector alignment score")
    compliance_score: float = Field(..., description="Compliance score")
    composite_score: float = Field(..., description="Composite score")
    evaluated_at: datetime = Field(..., description="Evaluation timestamp")
    summary_en: str = Field(..., description="English summary")
    summary_ar: str = Field(..., description="Arabic summary")


class EvaluationDetail(BaseModel):
    id: UUID = Field(..., description="Evaluation UUID")
    proposal_id: UUID = Field(..., description="Proposal UUID")
    relevance_score: float = Field(..., description="Relevance score")
    relevance_reasoning: str = Field(..., description="Relevance reasoning")
    feasibility_score: float = Field(..., description="Feasibility score")
    feasibility_reasoning: str = Field(..., description="Feasibility reasoning")
    sector_alignment_score: float = Field(..., description="Sector alignment score")
    sector_reasoning: str = Field(..., description="Sector reasoning")
    compliance_score: float = Field(..., description="Compliance score")
    compliance_reasoning: str = Field(..., description="Compliance reasoning")
    composite_score: float = Field(..., description="Composite score")
    evaluated_at: datetime = Field(..., description="Evaluation timestamp")
    evaluator_agent_versions: Optional[Dict[str, Any]] = Field(None, description="Agent version info")
    hallucination_check_passed: bool = Field(..., description="Hallucination check result")
    prompt_injection_detected: bool = Field(..., description="Prompt injection detection")
    summary_en: str = Field(..., description="English summary")
    summary_ar: str = Field(..., description="Arabic summary")
    ai_attribution: Optional[Dict[str, Any]] = Field(None, description="Dimension-level evidence attribution with evidence points, risks, and confidence")
    ai_interactions: List[AIInteractionInfo] = Field(default_factory=list, description="AI interactions")
