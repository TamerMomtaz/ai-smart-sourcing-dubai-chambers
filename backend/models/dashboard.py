from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class PipelineStatus(BaseModel):
    total_proposals: int = Field(..., description="Total proposals")
    submitted: int = Field(..., description="Submitted proposals")
    evaluating: int = Field(..., description="Evaluating proposals")
    under_review: int = Field(..., description="Under review proposals")
    approved: int = Field(..., description="Approved proposals")
    rejected: int = Field(..., description="Rejected proposals")


class SectorTrend(BaseModel):
    sector: str = Field(..., description="Sector name")
    proposal_count: int = Field(..., description="Number of proposals")
    average_score: float = Field(..., description="Average score")
    trend: Literal["up", "down", "stable"] = Field(..., description="Trend direction")


class D33Alignment(BaseModel):
    total_aligned_proposals: int = Field(..., description="Total aligned proposals")
    alignment_percentage: float = Field(..., description="Alignment percentage")
    top_alignment_areas: List[str] = Field(default_factory=list, description="Top alignment areas")


class VendorOnboardingFunnel(BaseModel):
    submission: int = Field(..., description="Submission stage count")
    shortlist: int = Field(..., description="Shortlist stage count")
    desc_badge_verify: int = Field(..., description="DESC badge verification stage count")
    pilot: int = Field(..., description="Pilot stage count")
    procurement_decision: int = Field(..., description="Procurement decision stage count")


class ComplianceSummary(BaseModel):
    total_audits: int = Field(..., description="Total audits")
    compliant: int = Field(..., description="Compliant audits")
    remediation_required: int = Field(..., description="Audits requiring remediation")


class ExecutiveDashboard(BaseModel):
    pipeline_status: PipelineStatus = Field(..., description="Pipeline status")
    sector_trends: List[SectorTrend] = Field(default_factory=list, description="Sector trends")
    d33_alignment: D33Alignment = Field(..., description="D33 alignment metrics")
    vendor_onboarding_funnel: VendorOnboardingFunnel = Field(..., description="Vendor onboarding funnel")
    compliance_summary: ComplianceSummary = Field(..., description="Compliance summary")


class PendingReview(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    title: str = Field(..., description="Proposal title")
    submission_date: datetime = Field(..., description="Submission timestamp")
    sector: str = Field(..., description="Sector")
    composite_score: float = Field(..., description="Composite score")
    requires_manual_review: bool = Field(..., description="Manual review flag")


class RecentEvaluation(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    title: str = Field(..., description="Proposal title")
    evaluated_at: datetime = Field(..., description="Evaluation timestamp")
    composite_score: float = Field(..., description="Composite score")


class DailyStats(BaseModel):
    proposals_reviewed: int = Field(..., description="Proposals reviewed")
    average_review_time_minutes: float = Field(..., description="Average review time in minutes")
    evaluations_triggered: int = Field(..., description="Evaluations triggered")


class AnalystDashboard(BaseModel):
    pending_reviews: List[PendingReview] = Field(default_factory=list, description="Pending reviews")
    recent_evaluations: List[RecentEvaluation] = Field(default_factory=list, description="Recent evaluations")
    daily_stats: DailyStats = Field(..., description="Daily statistics")


class AverageScores(BaseModel):
    relevance: float = Field(..., description="Average relevance score")
    feasibility: float = Field(..., description="Average feasibility score")
    sector_alignment: float = Field(..., description="Average sector alignment score")
    compliance: float = Field(..., description="Average compliance score")
    composite: float = Field(..., description="Average composite score")


class TechnologyDistribution(BaseModel):
    technology_type: str = Field(..., description="Technology type")
    count: int = Field(..., description="Number of proposals")


class MaturityDistribution(BaseModel):
    maturity_level: str = Field(..., description="Maturity level")
    count: int = Field(..., description="Number of proposals")


class TopProposal(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    title: str = Field(..., description="Proposal title")
    composite_score: float = Field(..., description="Composite score")
    vendor_name: str = Field(..., description="Vendor name")


class SectorDashboard(BaseModel):
    sector: str = Field(..., description="Sector name")
    total_proposals: int = Field(..., description="Total proposals")
    average_scores: AverageScores = Field(..., description="Average scores")
    technology_distribution: List[TechnologyDistribution] = Field(
        default_factory=list, description="Technology distribution"
    )
    maturity_distribution: List[MaturityDistribution] = Field(
        default_factory=list, description="Maturity distribution"
    )
    top_proposals: List[TopProposal] = Field(default_factory=list, description="Top proposals")
