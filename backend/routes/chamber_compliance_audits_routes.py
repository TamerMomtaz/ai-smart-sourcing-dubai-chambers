from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from models.compliance import (
    ComplianceAuditCreate,
    ComplianceAuditResponse,
    ComplianceAuditDetail,
    ComplianceReportResponse,
)
from models.common import PaginationResponse, ErrorResponse
from auth import get_current_user
from services import chamber_compliance_audits_service as compliance_service
from services import report_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance-audits",
    tags=["Compliance Audits"],
)


@router.post(
    "",
    response_model=ComplianceAuditResponse,
    status_code=201,
    summary="Create compliance audit",
    description="Create new compliance audit for a proposal. Compliance officer only.",
)
async def create_compliance_audit(
    audit_data: ComplianceAuditCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create compliance audit."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        # Verify compliance officer role
        if user_role not in ["compliance_officer", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only compliance officers can create audits",
                    "code": 403,
                },
            )

        # Create audit
        audit = compliance_service.create(
            user_id=user_id,
            proposal_id=audit_data.proposal_id,
            audit_type=audit_data.audit_type,
            auditor_user_id=user_id,
        )

        if not audit:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal Server Error",
                    "detail": "Failed to create compliance audit",
                    "code": 500,
                },
            )

        return ComplianceAuditResponse(
            audit_id=UUID(audit["id"]),
            proposal_id=UUID(audit["proposal_id"]),
            audit_type=audit["audit_type"],
            status=audit.get("status", "in_progress"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating compliance audit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to create compliance audit",
                "code": 500,
            },
        )


@router.get(
    "",
    response_model=dict,
    summary="List compliance audits",
    description="List all compliance audits with pagination. Filtered by user role and permissions.",
)
async def list_compliance_audits(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    proposal_id: Optional[UUID] = Query(None, description="Filter by proposal ID"),
    audit_type: Optional[str] = Query(None, description="Filter by audit type"),
    current_user: dict = Depends(get_current_user),
):
    """List compliance audits with pagination."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        # Only compliance officers, analysts, and executives can list audits
        if user_role not in ["compliance_officer", "analyst", "executive", "business_group_lead", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to view compliance audits",
                    "code": 403,
                },
            )

        result = compliance_service.list_audits(
            user_id=user_id,
            user_role=user_role,
            page=page,
            page_size=page_size,
            proposal_id=proposal_id,
            audit_type=audit_type,
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal Server Error",
                    "detail": "Failed to retrieve compliance audits",
                    "code": 500,
                },
            )

        total = result.get("total", 0)
        audits = result.get("audits", [])

        total_pages = (total + page_size - 1) // page_size

        return {
            "audits": audits,
            "pagination": PaginationResponse(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing compliance audits: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve compliance audits",
                "code": 500,
            },
        )


@router.get(
    "/{audit_id}",
    response_model=ComplianceAuditDetail,
    summary="Get compliance audit details",
    description="Get detailed compliance audit information by ID.",
)
async def get_compliance_audit(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get compliance audit by ID."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        # Only compliance officers, analysts, and executives can view audit details
        if user_role not in ["compliance_officer", "analyst", "executive", "business_group_lead", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to view audit details",
                    "code": 403,
                },
            )

        audit = compliance_service.get_by_id(
            user_id=user_id,
            audit_id=audit_id,
            user_role=user_role,
        )

        if not audit:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": "Compliance audit not found",
                    "code": 404,
                },
            )

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
            audit_report_url=audit.get("audit_report_url"),
            hash_chain_signature=audit.get("hash_chain_signature"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving compliance audit {audit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve compliance audit",
                "code": 500,
            },
        )


@router.put(
    "/{audit_id}",
    response_model=ComplianceAuditDetail,
    summary="Update compliance audit",
    description="Update compliance audit findings and results. Compliance officer only.",
)
async def update_compliance_audit(
    audit_id: UUID,
    audit_update: dict,
    current_user: dict = Depends(get_current_user),
):
    """Update compliance audit."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        # Verify compliance officer role
        if user_role not in ["compliance_officer", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only compliance officers can update audits",
                    "code": 403,
                },
            )

        updated_audit = compliance_service.update(
            user_id=user_id,
            audit_id=audit_id,
            update_data=audit_update,
        )

        if not updated_audit:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": "Compliance audit not found or update failed",
                    "code": 404,
                },
            )

        return ComplianceAuditDetail(
            id=UUID(updated_audit["id"]),
            proposal_id=UUID(updated_audit["proposal_id"]),
            audit_type=updated_audit["audit_type"],
            isr_v3_compliance=updated_audit.get("isr_v3_compliance", False),
            ai_security_policy_compliance=updated_audit.get("ai_security_policy_compliance", False),
            csp_standards_compliance=updated_audit.get("csp_standards_compliance", False),
            data_residency_verified=updated_audit.get("data_residency_verified", False),
            audit_timestamp=datetime.fromisoformat(updated_audit["audit_timestamp"]),
            auditor_user_id=UUID(updated_audit["auditor_user_id"]) if updated_audit.get("auditor_user_id") else None,
            findings=updated_audit.get("findings_json"),
            remediation_required=updated_audit.get("remediation_required", False),
            audit_report_url=updated_audit.get("audit_report_url"),
            hash_chain_signature=updated_audit.get("hash_chain_signature"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating compliance audit {audit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to update compliance audit",
                "code": 500,
            },
        )


@router.delete(
    "/{audit_id}",
    status_code=204,
    summary="Delete compliance audit",
    description="Delete compliance audit. Admin only. Compliance audits are normally immutable.",
)
async def delete_compliance_audit(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete compliance audit (admin only)."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        # Only admins can delete audits (immutability principle)
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only admins can delete compliance audits",
                    "code": 403,
                },
            )

        deleted = compliance_service.delete(
            user_id=user_id,
            audit_id=audit_id,
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": "Compliance audit not found or deletion failed",
                    "code": 404,
                },
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting compliance audit {audit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to delete compliance audit",
                "code": 500,
            },
        )


@router.post(
    "/{audit_id}/report",
    response_model=ComplianceReportResponse,
    summary="Generate compliance report",
    description="Generate DESC-format compliance audit report PDF with download URL.",
)
async def generate_compliance_report(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Generate compliance audit report."""
    try:
        user_id = current_user["id"]
        user_role = current_user.get("role", "")

        # Only compliance officers and executives can generate reports
        if user_role not in ["compliance_officer", "executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to generate reports",
                    "code": 403,
                },
            )

        report = report_service.generate_compliance_report(
            user_id=user_id,
            audit_id=audit_id,
        )

        if not report:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": "Compliance audit not found or report generation failed",
                    "code": 404,
                },
            )

        return ComplianceReportResponse(
            report_url=report["report_url"],
            expires_at=datetime.fromisoformat(report["expires_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report for audit {audit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to generate compliance report",
                "code": 500,
            },
        )
