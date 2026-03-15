from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from models.compliance import (
    ComplianceAuditCreate,
    ComplianceAuditResponse,
    ComplianceAuditDetail,
    ComplianceReportResponse,
)
from models.export import ExportResponse
from models.common import ErrorResponse
from auth import get_current_user
from services.compliance_audits_service import create_compliance_audit
from services.report_service import generate_compliance_report
from database import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/compliance-audits",
    tags=["compliance-audits"],
)


@router.post(
    "",
    response_model=ComplianceAuditResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only compliance officers can trigger audits"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
    },
)
async def trigger_compliance_audit(
    request: ComplianceAuditCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger compliance audit for proposal (compliance officer only).
    
    Creates a new compliance audit with specified audit type.
    Only accessible to users with compliance_officer role.
    
    Args:
        request: ComplianceAuditCreate with proposal_id and audit_type
        current_user: Authenticated user from JWT
    
    Returns:
        ComplianceAuditResponse with audit_id, proposal_id, audit_type, and status
    
    Raises:
        401: If user is not authenticated
        403: If user is not a compliance officer
        404: If proposal not found
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()
        
        if user_role != "compliance_officer":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only compliance officers can trigger compliance audits",
                    "code": "ROLE_COMPLIANCE_OFFICER_REQUIRED",
                },
            )
        
        # Verify proposal exists
        proposal_response = (
            supabase.table("chamber_proposals")
            .select("id, status")
            .eq("id", str(request.proposal_id))
            .maybe_single()
            .execute()
        )
        
        if not proposal_response.data:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "detail": f"Proposal {request.proposal_id} not found",
                    "code": "PROPOSAL_NOT_FOUND",
                },
            )
        
        # Create compliance audit
        audit = create_compliance_audit(
            user_id=user_id,
            proposal_id=request.proposal_id,
            audit_type=request.audit_type.strip(),
            auditor_user_id=user_id,
        )
        
        if not audit:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "detail": "Failed to create compliance audit",
                    "code": "AUDIT_CREATION_FAILED",
                },
            )
        
        return ComplianceAuditResponse(
            audit_id=UUID(audit["id"]),
            proposal_id=UUID(audit["proposal_id"]),
            audit_type=audit["audit_type"],
            status="in_progress",
        )
    
    except ValueError as ve:
        logger.error(f"Validation error in trigger_compliance_audit: {ve}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "detail": str(ve),
                "code": "VALIDATION_ERROR",
            },
        )
    except Exception as e:
        logger.error(f"Error triggering compliance audit: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while triggering compliance audit",
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/{audit_id}",
    response_model=ComplianceAuditDetail,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Audit not found"},
    },
)
async def get_compliance_audit(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get compliance audit details and report.
    
    Retrieves full audit details including compliance flags, findings,
    and hash chain signature.
    
    Args:
        audit_id: UUID of the compliance audit
        current_user: Authenticated user from JWT
    
    Returns:
        ComplianceAuditDetail with full audit information
    
    Raises:
        401: If user is not authenticated
        403: If user lacks permission to view audit
        404: If audit not found
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()
        
        # Query audit with proposal details for permission check
        audit_response = (
            supabase.table("chamber_compliance_audits")
            .select(
                "id, proposal_id, audit_type, isr_v3_compliance, "
                "ai_security_policy_compliance, csp_standards_compliance, "
                "data_residency_verified, audit_timestamp, auditor_user_id, "
                "findings_json, remediation_required, audit_report_path, "
                "hash_chain_signature, chamber_proposals!inner(id, submitter_id, business_group_id)"
            )
            .eq("id", str(audit_id))
            .maybe_single()
            .execute()
        )
        
        if not audit_response.data:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "detail": f"Compliance audit {audit_id} not found",
                    "code": "AUDIT_NOT_FOUND",
                },
            )
        
        audit = audit_response.data
        proposal = audit.get("chamber_proposals", {})
        
        # Permission check: compliance_officer, executive, or analysts can view
        # Vendors can only view their own proposal audits
        if user_role == "vendor":
            if str(proposal.get("submitter_id")) != str(user_id):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Forbidden",
                        "detail": "You can only view audits for your own proposals",
                        "code": "INSUFFICIENT_PERMISSIONS",
                    },
                )
        elif user_role == "business_group_lead":
            # Business group leads can only view audits for their sector
            user_bg_response = (
                supabase.table("chamber_users")
                .select("business_group_id")
                .eq("id", str(user_id))
                .maybe_single()
                .execute()
            )
            if user_bg_response.data:
                user_bg_id = user_bg_response.data.get("business_group_id")
                if user_bg_id and str(proposal.get("business_group_id")) != str(user_bg_id):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "Forbidden",
                            "detail": "You can only view audits for proposals in your business group",
                            "code": "INSUFFICIENT_PERMISSIONS",
                        },
                    )
        elif user_role not in ["analyst", "compliance_officer", "executive", "admin"]:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to view this audit",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )
        
        # Generate audit report URL if available
        audit_report_url = None
        if audit.get("audit_report_path"):
            # Generate signed URL for report download
            try:
                signed_url_response = supabase.storage.from_("compliance-reports").create_signed_url(
                    audit["audit_report_path"],
                    3600,  # 1 hour expiry
                )
                if signed_url_response:
                    audit_report_url = signed_url_response.get("signedURL")
            except Exception as url_error:
                logger.warning(f"Failed to generate signed URL for audit report: {url_error}")
        
        return ComplianceAuditDetail(
            id=UUID(audit["id"]),
            proposal_id=UUID(audit["proposal_id"]),
            audit_type=audit["audit_type"],
            isr_v3_compliance=audit.get("isr_v3_compliance", False),
            ai_security_policy_compliance=audit.get("ai_security_policy_compliance", False),
            csp_standards_compliance=audit.get("csp_standards_compliance", False),
            data_residency_verified=audit.get("data_residency_verified", False),
            audit_timestamp=datetime.fromisoformat(audit["audit_timestamp"]),
            auditor_user_id=UUID(audit["auditor_user_id"]) if audit.get("auditor_user_id") else None,
            findings=audit.get("findings_json"),
            remediation_required=audit.get("remediation_required", False),
            audit_report_url=audit_report_url,
            hash_chain_signature=audit.get("hash_chain_signature"),
        )
    
    except ValueError as ve:
        logger.error(f"Validation error in get_compliance_audit: {ve}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "detail": str(ve),
                "code": "VALIDATION_ERROR",
            },
        )
    except Exception as e:
        logger.error(f"Error retrieving compliance audit: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while retrieving audit details",
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/{audit_id}/report",
    response_model=ComplianceReportResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only compliance officers can download reports"},
        404: {"model": ErrorResponse, "description": "Audit report not found"},
    },
)
async def download_compliance_report(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Download DESC-format compliance audit report PDF.
    
    Generates a temporary signed URL for downloading the audit report.
    Only accessible to compliance officers.
    
    Args:
        audit_id: UUID of the compliance audit
        current_user: Authenticated user from JWT
    
    Returns:
        ComplianceReportResponse with report_url and expires_at
    
    Raises:
        401: If user is not authenticated
        403: If user is not a compliance officer
        404: If audit report not found
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()
        
        if user_role != "compliance_officer":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only compliance officers can download audit reports",
                    "code": "ROLE_COMPLIANCE_OFFICER_REQUIRED",
                },
            )
        
        report_result = generate_compliance_report(
            user_id=str(user_id),
            audit_id=audit_id,
        )
        
        if not report_result:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "detail": f"Compliance audit report for {audit_id} not found",
                    "code": "AUDIT_REPORT_NOT_FOUND",
                },
            )
        
        return ComplianceReportResponse(
            report_url=report_result["report_url"],
            expires_at=datetime.fromisoformat(report_result["expires_at"]),
        )
    
    except ValueError as ve:
        logger.error(f"Validation error in download_compliance_report: {ve}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "detail": str(ve),
                "code": "VALIDATION_ERROR",
            },
        )
    except Exception as e:
        logger.error(f"Error downloading compliance report: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while generating report download URL",
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/export/compliance-audits",
    response_model=ExportResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - compliance officer role required"},
    },
)
async def export_compliance_audits(
    current_user: dict = Depends(get_current_user),
):
    """
    Export compliance audit history as DESC-format report (compliance officer only).
    
    Generates a comprehensive audit trail export with hash chain signatures
    for regulatory compliance documentation.
    
    Args:
        current_user: Authenticated user from JWT
    
    Returns:
        ExportResponse with export_url, expires_at, and hash_chain_signature
    
    Raises:
        401: If user is not authenticated
        403: If user is not a compliance officer
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()
        
        if user_role != "compliance_officer":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only compliance officers can export audit history",
                    "code": "ROLE_COMPLIANCE_OFFICER_REQUIRED",
                },
            )
        
        # Query all compliance audits with proposal context
        audits_response = (
            supabase.table("chamber_compliance_audits")
            .select(
                "id, proposal_id, audit_type, isr_v3_compliance, "
                "ai_security_policy_compliance, csp_standards_compliance, "
                "data_residency_verified, audit_timestamp, auditor_user_id, "
                "remediation_required, hash_chain_signature, "
                "chamber_proposals!inner(id, title, sector, submitter_id, chamber_vendors(name))"
            )
            .order("audit_timestamp", desc=True)
            .execute()
        )
        
        if not audits_response.data:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "detail": "No compliance audits found for export",
                    "code": "NO_AUDITS_FOUND",
                },
            )
        
        # Generate export file in storage
        import csv
        import hashlib
        from io import StringIO
        from datetime import timedelta
        
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # CSV Headers
        csv_writer.writerow([
            "Audit ID",
            "Proposal ID",
            "Proposal Title",
            "Vendor Name",
            "Sector",
            "Audit Type",
            "Audit Timestamp",
            "ISR V3 Compliance",
            "AI Security Policy Compliance",
            "CSP Standards Compliance",
            "Data Residency Verified",
            "Remediation Required",
            "Hash Chain Signature",
        ])
        
        for audit in audits_response.data:
            proposal = audit.get("chamber_proposals", {})
            vendor = proposal.get("chamber_vendors", {})
            
            csv_writer.writerow([
                audit["id"],
                audit["proposal_id"],
                proposal.get("title", ""),
                vendor.get("name", ""),
                proposal.get("sector", ""),
                audit["audit_type"],
                audit["audit_timestamp"],
                audit.get("isr_v3_compliance", False),
                audit.get("ai_security_policy_compliance", False),
                audit.get("csp_standards_compliance", False),
                audit.get("data_residency_verified", False),
                audit.get("remediation_required", False),
                audit.get("hash_chain_signature", ""),
            ])
        
        csv_content = csv_buffer.getvalue()
        
        # Generate hash chain signature for export
        export_hash = hashlib.sha256(csv_content.encode()).hexdigest()
        
        # Upload to Supabase Storage
        export_filename = f"compliance_audit_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        
        upload_response = supabase.storage.from_("compliance-reports").upload(
            export_filename,
            csv_content.encode(),
            {"content-type": "text/csv"},
        )
        
        if not upload_response:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "detail": "Failed to upload export file to storage",
                    "code": "EXPORT_UPLOAD_FAILED",
                },
            )
        
        # Generate signed URL
        signed_url_response = supabase.storage.from_("compliance-reports").create_signed_url(
            export_filename,
            3600,  # 1 hour expiry
        )
        
        if not signed_url_response:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "detail": "Failed to generate signed URL for export",
                    "code": "SIGNED_URL_FAILED",
                },
            )
        
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        return ExportResponse(
            export_url=signed_url_response["signedURL"],
            expires_at=expires_at,
            format="csv",
            hash_chain_signature=export_hash,
        )
    
    except Exception as e:
        logger.error(f"Error exporting compliance audits: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while exporting audit history",
                "code": "INTERNAL_ERROR",
            },
        )
