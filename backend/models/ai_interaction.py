from typing import List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class RecentInteraction(BaseModel):
    id: UUID = Field(..., description="Interaction UUID")
    timestamp: datetime = Field(..., description="Interaction timestamp")
    model_name: str = Field(..., description="AI model name")
    operation_type: str = Field(..., description="Operation type")
    prompt_tokens: int = Field(..., description="Prompt tokens")
    completion_tokens: int = Field(..., description="Completion tokens")
    latency_ms: int = Field(..., description="Response latency in ms")
    cost_usd: float = Field(..., description="Cost in USD")


class ModelBreakdown(BaseModel):
    model_name: str = Field(..., description="AI model name")
    interaction_count: int = Field(..., description="Number of interactions")
    total_tokens: int = Field(..., description="Total tokens used")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    average_latency_ms: float = Field(..., description="Average latency in ms")


class AIInteractionSummary(BaseModel):
    total_interactions: int = Field(..., description="Total interactions")
    total_tokens: int = Field(..., description="Total tokens")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    total_energy_kwh: float = Field(..., description="Total energy consumption in kWh")
    total_carbon_gco2: float = Field(..., description="Total carbon emissions in gCO2")
    total_intelligence_units: float = Field(..., description="Total intelligence units")
    model_breakdown: List[ModelBreakdown] = Field(default_factory=list, description="Model breakdown")
    recent_interactions: List[RecentInteraction] = Field(default_factory=list, description="Recent interactions")


class AIInteractionResponse(BaseModel):
    total_interactions: int = Field(..., description="Total interactions")
    total_tokens: int = Field(..., description="Total tokens")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    total_energy_kwh: float = Field(..., description="Total energy in kWh")
    total_carbon_gco2: float = Field(..., description="Total carbon in gCO2")
    total_intelligence_units: float = Field(..., description="Total intelligence units")
    model_breakdown: List[ModelBreakdown] = Field(default_factory=list, description="Model breakdown")
    recent_interactions: List[RecentInteraction] = Field(default_factory=list, description="Recent interactions")
