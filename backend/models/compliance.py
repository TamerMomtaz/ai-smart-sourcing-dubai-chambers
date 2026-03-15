from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date


class ComplianceAuditCreate(BaseModel):
    proposal_id: UUID = Field(..., description="Proposal UUID")
    audit_type: Literal[
        "isr_v3",
        "ai_security_policy",
        "csp_standards",
        "comprehensive",
    ] = Field(..., description="Audit type")


class ComplianceAuditResponse(BaseModel):
    audit_id: UUID = Field(..., description="Audit UUID")
    proposal_id: UUID = Field(..., description="Proposal UUID")
    audit_type: str = Field(..., description="Audit type")
    status: str = Field(default="in_progress", description="Audit status")


class ComplianceAuditDetail(BaseModel):
    id: UUID = Field(..., description="Audit UUID")
    proposal_id: UUID = Field(..., description="Proposal UUID")
    audit_type: str = Field(..., description="Audit type")
    isr_v3_compliance: bool = Field(..., description="ISR V3 compliance")
    ai_security_policy_compliance: bool = Field(..., description="AI security policy compliance")
    csp_standards_compliance: bool = Field(..., description="CSP standards compliance")
    data_residency_verified: bool = Field(..., description="Data residency verified")
    audit_timestamp: datetime = Field(..., description="Audit timestamp")
    auditor_user_id: Optional[UUID] = Field(None, description="Auditor user ID")
    findings: Optional[Dict[str, Any]] = Field(None, description="Audit findings")
    remediation_required: bool = Field(..., description="Remediation required")
    audit_report_url: Optional[str] = Field(None, description="Audit report URL")
    hash_chain_signature: Optional[str] = Field(None, description="Hash chain signature")


class ComplianceReportResponse(BaseModel):
    report_url: str = Field(..., description="Report download URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")


class CertifiedProvider(BaseModel):
    id: UUID = Field(..., description="Provider UUID")
    provider_name: str = Field(..., description="Provider name")
    certification_number: str = Field(..., description="Certification number")
    valid_until: date = Field(..., description="Certification expiry date")
    services_offered: List[str] = Field(default_factory=list, description="Certified services")
    compliance_frameworks: List[str] = Field(default_factory=list, description="Compliance frameworks")


class CertifiedProviderVerifyRequest(BaseModel):
    vendor_id: UUID = Field(..., description="Vendor UUID to verify")


class CertificationDetails(BaseModel):
    certification_number: str = Field(..., description="Certification number")
    valid_until: date = Field(..., description="Valid until date")
    compliance_frameworks: List[str] = Field(default_factory=list, description="Compliance frameworks")


class CertifiedProviderVerifyResponse(BaseModel):
    vendor_id: UUID = Field(..., description="Vendor UUID")
    is_certified: bool = Field(..., description="Certification status")
    certification_details: Optional[CertificationDetails] = Field(None, description="Certification details")
