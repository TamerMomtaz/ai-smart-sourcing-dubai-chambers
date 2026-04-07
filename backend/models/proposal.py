from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from models.common import PaginationResponse


class ProposalCreate(BaseModel):
    title: str = Field(..., max_length=255, description="Proposal title")
    sector: Literal[
        "fintech",
        "healthcare",
        "logistics",
        "energy",
        "education",
        "government",
        "tourism",
        "other",
    ] = Field(..., description="Industry sector")
    technology_type: Literal[
        "ai_ml",
        "blockchain",
        "iot",
        "cloud",
        "cybersecurity",
        "data_analytics",
        "other",
    ] = Field(..., description="Technology category")
    maturity_level: Literal[
        "concept",
        "prototype",
        "mvp",
        "production",
        "scaling",
    ] = Field(..., description="Product maturity stage")
    language: Literal["en", "ar"] = Field(..., description="Proposal language")
    business_group_id: Optional[UUID] = Field(None, description="Target business group ID")
    description: Optional[str] = Field(None, description="Proposal description")
    sourcing_case_id: Optional[UUID] = Field(None, description="Linked sourcing case ID")


class DocumentUploadInfo(BaseModel):
    document_id: UUID = Field(..., description="Document UUID")
    upload_url: str = Field(..., description="Pre-signed upload URL")


class ProposalResponse(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    status: str = Field(..., description="Proposal status")
    upload_urls: List[DocumentUploadInfo] = Field(default_factory=list, description="Document upload URLs")


class ProposalSubmitResponse(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    status: str = Field(default="queued_for_evaluation", description="Proposal status")
    estimated_completion: datetime = Field(..., description="Estimated completion timestamp")


class ProposalListItem(BaseModel):
    id: UUID = Field(..., description="Proposal UUID")
    title: str = Field(..., description="Proposal title")
    submitter_id: UUID = Field(..., description="Vendor ID")
    submission_date: datetime = Field(..., description="Submission timestamp")
    status: str = Field(..., description="Proposal status")
    sector: str = Field(..., description="Industry sector")
    technology_type: str = Field(..., description="Technology category")
    maturity_level: str = Field(..., description="Maturity stage")
    composite_score: Optional[float] = Field(None, description="Composite score")
    is_duplicate: bool = Field(..., description="Duplicate flag")
    requires_manual_review: bool = Field(..., description="Manual review flag")


class ProposalListResponse(BaseModel):
    proposals: List[ProposalListItem] = Field(..., description="List of proposals")
    pagination: PaginationResponse = Field(..., description="Pagination metadata")


class VendorInfo(BaseModel):
    id: UUID = Field(..., description="Vendor UUID")
    name: str = Field(..., description="Vendor name")
    company_registration: str = Field(..., description="Company registration")
    is_desc_approved: bool = Field(..., description="DESC approval status")


class DocumentInfo(BaseModel):
    id: UUID = Field(..., description="Document UUID")
    file_name: str = Field(..., description="File name")
    file_type: str = Field(..., description="File type")
    file_size: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class EvaluationInfo(BaseModel):
    relevance_reasoning: str = Field(..., description="Relevance reasoning")
    feasibility_reasoning: str = Field(..., description="Feasibility reasoning")
    sector_reasoning: str = Field(..., description="Sector reasoning")
    compliance_reasoning: str = Field(..., description="Compliance reasoning")
    summary_en: str = Field(..., description="English summary")
    summary_ar: str = Field(..., description="Arabic summary")
    hallucination_check_passed: bool = Field(..., description="Hallucination check result")
    prompt_injection_detected: bool = Field(..., description="Prompt injection detection")


class ComplianceAuditInfo(BaseModel):
    id: UUID = Field(..., description="Audit UUID")
    audit_type: str = Field(..., description="Audit type")
    isr_v3_compliance: bool = Field(..., description="ISR V3 compliance")
    ai_security_policy_compliance: bool = Field(..., description="AI security policy compliance")
    csp_standards_compliance: bool = Field(..., description="CSP standards compliance")
    data_residency_verified: bool = Field(..., description="Data residency verified")
    audit_timestamp: datetime = Field(..., description="Audit timestamp")
    remediation_required: bool = Field(..., description="Remediation required")


class CommentInfo(BaseModel):
    id: UUID = Field(..., description="Comment UUID")
    user_id: UUID = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    comment_text: str = Field(..., description="Comment text")
    created_at: datetime = Field(..., description="Creation timestamp")
    visibility: str = Field(..., description="Comment visibility")


class ProposalDetail(BaseModel):
    id: UUID = Field(..., description="Proposal UUID")
    title: str = Field(..., description="Proposal title")
    submitter_id: UUID = Field(..., description="Vendor ID")
    vendor: VendorInfo = Field(..., description="Vendor information")
    submission_date: datetime = Field(..., description="Submission timestamp")
    status: str = Field(..., description="Proposal status")
    sector: str = Field(..., description="Industry sector")
    technology_type: str = Field(..., description="Technology category")
    maturity_level: str = Field(..., description="Maturity stage")
    language: str = Field(..., description="Proposal language")
    composite_score: Optional[float] = Field(None, description="Composite score")
    relevance_score: Optional[float] = Field(None, description="Relevance score")
    feasibility_score: Optional[float] = Field(None, description="Feasibility score")
    sector_alignment_score: Optional[float] = Field(None, description="Sector alignment score")
    compliance_score: Optional[float] = Field(None, description="Compliance score")
    evaluation_timestamp: Optional[datetime] = Field(None, description="Evaluation timestamp")
    is_duplicate: bool = Field(..., description="Duplicate flag")
    requires_manual_review: bool = Field(..., description="Manual review flag")
    d33_alignment_metrics: Optional[Dict[str, Any]] = Field(None, description="D33 alignment metrics")
    documents: List[DocumentInfo] = Field(default_factory=list, description="Attached documents")
    evaluation: Optional[EvaluationInfo] = Field(None, description="Evaluation details")
    compliance_audits: List[ComplianceAuditInfo] = Field(default_factory=list, description="Compliance audits")
    comments: List[CommentInfo] = Field(default_factory=list, description="Comments")


class ProposalStatusUpdate(BaseModel):
    status: Literal[
        "under_review",
        "approved",
        "rejected",
        "requires_manual_review",
    ] = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Status change reason")


class ProposalStatusUpdateResponse(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    status: str = Field(..., description="Updated status")
    updated_at: datetime = Field(..., description="Update timestamp")


class ProposalEvaluateResponse(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    status: str = Field(default="queued_for_evaluation", description="Proposal status")
    job_id: UUID = Field(..., description="Evaluation job ID")


class SimilarProposal(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    title: str = Field(..., description="Proposal title")
    similarity_score: float = Field(..., description="Similarity score")
    submission_date: datetime = Field(..., description="Submission timestamp")


class DuplicateCheckResponse(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    is_duplicate: bool = Field(..., description="Duplicate flag")
    similar_proposals: List[SimilarProposal] = Field(default_factory=list, description="Similar proposals")
