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

        # Vendor role gets empty list (no access to compliance audit data)
        if user_role not in ["compliance_officer", "analyst", "executive", "business_group_lead", "admin"]:
            return {
                "audits": [],
                "pagination": PaginationResponse(
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                ),
            }

        audits, total = compliance_service.list_audits(
            user_id=user_id,
            user_role=user_role,
            page=page,
            page_size=page_size,
            proposal_id=proposal_id,
            audit_type=audit_type,
        )

        if audits is None:
            audits = []
            total = 0

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


@router.get(
    "/{audit_id}/report-data",
    summary="Get audit report data",
    description="Get structured data for DESC compliance audit PDF report.",
)
async def get_audit_report_data(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Return structured audit data for the printable report page."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        if user_role not in ["compliance_officer", "analyst", "executive", "business_group_lead", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to view audit report",
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

        # Fetch proposal details with vendor name via join
        from database import supabase as db
        proposal_data = (
            db.table("chamber_proposals")
            .select("id,title,sector,submitter_id,created_at,submitter:chamber_vendors(name)")
            .eq("id", str(audit["proposal_id"]))
            .execute()
        )
        proposal = proposal_data.data[0] if proposal_data.data else {}
        # Resolve vendor_name from the joined submitter relation
        vendor_name = "Unknown Vendor"
        if proposal.get("submitter") and isinstance(proposal["submitter"], dict):
            vendor_name = proposal["submitter"].get("name", "Unknown Vendor")
        elif proposal.get("submitter_id"):
            vendor_data = (
                db.table("chamber_vendors")
                .select("name")
                .eq("id", str(proposal["submitter_id"]))
                .execute()
            )
            if vendor_data.data:
                vendor_name = vendor_data.data[0].get("name", "Unknown Vendor")

        # Fetch auditor name
        auditor_name = "AI Smart Sourcing"
        if audit.get("auditor_user_id"):
            auditor_data = (
                db.table("chamber_users")
                .select("email")
                .eq("id", str(audit["auditor_user_id"]))
                .execute()
            )
            if auditor_data.data:
                auditor_name = auditor_data.data[0].get("email", auditor_name)

        # Parse findings
        findings = audit.get("findings_json") or {}
        if isinstance(findings, str):
            import json
            try:
                findings = json.loads(findings)
            except Exception:
                findings = {}

        frameworks_raw = findings.get("frameworks", [])
        overall_score = findings.get("overall_score", audit.get("overall_score"))
        overall_status = findings.get("overall_status", audit.get("overall_status"))
        summary_text = findings.get("summary", audit.get("summary", ""))

        # Build per-framework results
        framework_results = []
        total_pass = 0
        total_fail = 0
        total_warn = 0
        for fw in frameworks_raw:
            controls = fw.get("controls", [])
            fw_pass = sum(1 for c in controls if c.get("status") == "pass")
            fw_fail = sum(1 for c in controls if c.get("status") == "fail")
            fw_warn = sum(1 for c in controls if c.get("status") == "warning")
            total_pass += fw_pass
            total_fail += fw_fail
            total_warn += fw_warn
            fw_total = len(controls)
            fw_score = round((fw_pass / max(fw_total, 1)) * 100, 1)
            framework_results.append({
                "name": fw.get("name", "Unknown Framework"),
                "controls": controls,
                "pass_count": fw_pass,
                "fail_count": fw_fail,
                "warning_count": fw_warn,
                "sub_score": fw_score,
            })

        # If no frameworks in findings, build from the boolean flags
        if not framework_results:
            def _flag_framework(name, flag_key):
                passed = bool(audit.get(flag_key, False))
                return {
                    "name": name,
                    "controls": [{
                        "control_id": flag_key,
                        "control_name": name + " Compliance",
                        "status": "pass" if passed else "fail",
                        "evidence": "Verified during audit" if passed else "Not verified",
                        "recommendation": "" if passed else "Requires review",
                    }],
                    "pass_count": 1 if passed else 0,
                    "fail_count": 0 if passed else 1,
                    "warning_count": 0,
                    "sub_score": 100.0 if passed else 0.0,
                }
            framework_results = [
                _flag_framework("ISR V3", "isr_v3_compliance"),
                _flag_framework("AI Security Policy", "ai_security_policy_compliance"),
                _flag_framework("CSP Standards", "csp_standards_compliance"),
            ]
            total_pass = sum(f["pass_count"] for f in framework_results)
            total_fail = sum(f["fail_count"] for f in framework_results)

        # Compute overall score if missing
        if overall_score is None:
            total_controls = total_pass + total_fail + total_warn
            overall_score = round((total_pass / max(total_controls, 1)) * 100, 1)

        # Determine compliance label
        if overall_score >= 80:
            compliance_label = "Compliant"
            risk_level = "low"
        elif overall_score >= 60:
            compliance_label = "Conditionally Compliant"
            risk_level = "medium"
        else:
            compliance_label = "Non-Compliant"
            risk_level = "high"

        # DESC AI Security Lifecycle phases
        lifecycle_phases = findings.get("ai_security_lifecycle", [
            {"phase": "Design", "status": "pass" if audit.get("ai_security_policy_compliance") else "fail"},
            {"phase": "Develop", "status": "pass" if audit.get("ai_security_policy_compliance") else "fail"},
            {"phase": "Deploy", "status": "pass" if audit.get("csp_standards_compliance") else "fail"},
            {"phase": "Monitor", "status": "pass" if audit.get("isr_v3_compliance") else "fail"},
            {"phase": "Dispose", "status": "warning"},
        ])

        # Remediation items
        remediation_items = []
        if total_fail > 0 or audit.get("remediation_required"):
            for fw in framework_results:
                for ctrl in fw.get("controls", []):
                    if ctrl.get("status") == "fail":
                        remediation_items.append({
                            "framework": fw["name"],
                            "control_id": ctrl.get("control_id", ""),
                            "control_name": ctrl.get("control_name", ""),
                            "recommendation": ctrl.get("recommendation", "Review required"),
                            "priority": "high",
                        })
                    elif ctrl.get("status") == "warning":
                        remediation_items.append({
                            "framework": fw["name"],
                            "control_id": ctrl.get("control_id", ""),
                            "control_name": ctrl.get("control_name", ""),
                            "recommendation": ctrl.get("recommendation", "Improvement recommended"),
                            "priority": "medium",
                        })

        data_residency = findings.get("data_residency", {})
        vendor_certification = findings.get("vendor_certification", {})

        return {
            "audit_id": str(audit["id"]),
            "proposal_title": proposal.get("title", "Unknown Proposal"),
            "vendor_name": vendor_name,
            "sector": proposal.get("sector", ""),
            "audit_date": audit.get("audit_timestamp", ""),
            "auditor": auditor_name,
            "audit_type": audit.get("audit_type", "comprehensive"),
            "overall_score": overall_score,
            "compliance_label": compliance_label,
            "risk_level": risk_level,
            "summary": summary_text,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "total_warnings": total_warn,
            "frameworks": framework_results,
            "remediation_items": remediation_items,
            "remediation_required": audit.get("remediation_required", False),
            "lifecycle_phases": lifecycle_phases,
            "data_residency": {
                "verified": bool(audit.get("data_residency_verified", False)),
                "details": data_residency,
            },
            "vendor_certification": vendor_certification,
            "hash_chain_signature": audit.get("hash_chain_signature", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building audit report data for {audit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to build audit report data",
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
