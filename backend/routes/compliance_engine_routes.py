"""Routes for AI-powered DESC compliance audit execution."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from auth import get_current_user
from services.compliance_engine import ComplianceEngine
from services import chamber_compliance_audits_service as compliance_service
from database import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/proposals",
    tags=["Compliance Audit Engine"],
)


@router.post(
    "/{proposal_id}/audit",
    summary="Run DESC compliance audit",
    description="Run an AI-powered DESC compliance audit on a proposal. Admin or compliance_officer only.",
)
async def run_compliance_audit(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Execute a full DESC compliance audit using Claude AI."""
    try:
        user_id = str(current_user["id"])
        user_role = current_user.get("role", "")

        allowed_roles = ["compliance_officer", "analyst", "executive", "business_group_lead", "admin"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to run compliance audits",
                    "code": 403,
                },
            )

        engine = ComplianceEngine()
        result = await engine.run_audit(
            proposal_id=str(proposal_id),
            user_id=user_id,
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Bad Request",
                "detail": str(e),
                "code": 400,
            },
        )
    except Exception as e:
        logger.error(f"Error running compliance audit for proposal {proposal_id}: {e}")
        is_ai_failure = "All AI providers failed" in str(e)
        raise HTTPException(
            status_code=503 if is_ai_failure else 500,
            detail={"error": "AI service temporarily busy. Please try again in 1-2 minutes."} if is_ai_failure else {
                "error": "Internal Server Error",
                "detail": "Failed to run compliance audit",
                "code": 500,
            },
        )


# Enhanced list endpoint with proposal title join
list_router = APIRouter(
    prefix="/compliance-audit-results",
    tags=["Compliance Audit Results"],
)


@list_router.get(
    "",
    summary="List compliance audit results with proposal titles",
    description="List all compliance audit results with proposal title, score, and status.",
)
async def list_audit_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    sort_by: Optional[str] = Query("audit_timestamp", regex="^(audit_timestamp|overall_score)$"),
    current_user: dict = Depends(get_current_user),
):
    """List compliance audit results with proposal titles and scores."""
    try:
        user_role = current_user.get("role", "")

        if user_role not in ["compliance_officer", "analyst", "executive", "business_group_lead", "admin"]:
            return {"audits": [], "pagination": {"total": 0, "page": page, "page_size": page_size, "total_pages": 0}}

        offset = (page - 1) * page_size

        query = supabase.table("chamber_compliance_audits").select("*", count="exact")

        if status_filter:
            query = query.eq("findings_json->>overall_status", status_filter)

        # Sort — for overall_score we sort by the JSON field via audit_timestamp fallback
        query = query.order("audit_timestamp", desc=True)
        query = query.range(offset, offset + page_size - 1)

        response = query.execute()
        audits = response.data or []
        total = response.count if hasattr(response, "count") and response.count else 0

        # Fetch proposal titles for all audit proposal_ids
        proposal_ids = list({a["proposal_id"] for a in audits if a.get("proposal_id")})
        proposal_map = {}
        if proposal_ids:
            prop_result = (
                supabase.table("chamber_proposals")
                .select("id, title")
                .in_("id", proposal_ids)
                .execute()
            )
            for p in (prop_result.data or []):
                proposal_map[p["id"]] = p["title"]

        # Enrich audits with proposal title and parsed findings
        enriched = []
        for a in audits:
            findings = a.get("findings_json")
            if isinstance(findings, str):
                try:
                    findings = __import__("json").loads(findings)
                except Exception:
                    findings = {}
            elif findings is None:
                findings = {}

            enriched.append({
                "id": a["id"],
                "proposal_id": a["proposal_id"],
                "proposal_title": proposal_map.get(a["proposal_id"], "Unknown"),
                "audit_type": a.get("audit_type"),
                "overall_score": findings.get("overall_score"),
                "overall_status": findings.get("overall_status"),
                "isr_v3_compliance": a.get("isr_v3_compliance", False),
                "ai_security_policy_compliance": a.get("ai_security_policy_compliance", False),
                "csp_standards_compliance": a.get("csp_standards_compliance", False),
                "data_residency_verified": a.get("data_residency_verified", False),
                "remediation_required": a.get("remediation_required", False),
                "audit_timestamp": a.get("audit_timestamp"),
                "summary": findings.get("summary", ""),
            })

        # Sort by score if requested
        if sort_by == "overall_score":
            enriched.sort(key=lambda x: x.get("overall_score") or 0, reverse=True)

        # Filter by status if requested (post-filter for JSON field)
        if status_filter:
            enriched = [a for a in enriched if a.get("overall_status") == status_filter]
            total = len(enriched)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "audits": enriched,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }

    except Exception as e:
        logger.error(f"Error listing audit results: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve audit results",
                "code": 500,
            },
        )


@list_router.get(
    "/{audit_id}",
    summary="Get compliance audit result detail",
    description="Get full compliance audit detail with framework controls.",
)
async def get_audit_result(
    audit_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get detailed compliance audit result including all framework controls."""
    try:
        user_role = current_user.get("role", "")

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
            user_id=current_user["id"],
            audit_id=audit_id,
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

        # Get proposal title
        proposal_title = "Unknown"
        if audit.get("proposal_id"):
            prop_result = (
                supabase.table("chamber_proposals")
                .select("title")
                .eq("id", audit["proposal_id"])
                .maybe_single()
                .execute()
            )
            if prop_result.data:
                proposal_title = prop_result.data.get("title", "Unknown")

        findings = audit.get("findings_json")
        if isinstance(findings, str):
            try:
                findings = __import__("json").loads(findings)
            except Exception:
                findings = {}
        elif findings is None:
            findings = {}

        return {
            "id": audit["id"],
            "proposal_id": audit["proposal_id"],
            "proposal_title": proposal_title,
            "audit_type": audit.get("audit_type"),
            "isr_v3_compliance": audit.get("isr_v3_compliance", False),
            "ai_security_policy_compliance": audit.get("ai_security_policy_compliance", False),
            "csp_standards_compliance": audit.get("csp_standards_compliance", False),
            "data_residency_verified": audit.get("data_residency_verified", False),
            "remediation_required": audit.get("remediation_required", False),
            "audit_timestamp": audit.get("audit_timestamp"),
            "auditor_user_id": audit.get("auditor_user_id"),
            "frameworks": findings.get("frameworks", []),
            "data_residency": findings.get("data_residency", {}),
            "vendor_certification": findings.get("vendor_certification", {}),
            "overall_score": findings.get("overall_score"),
            "overall_status": findings.get("overall_status"),
            "summary": findings.get("summary", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit result {audit_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve audit result",
                "code": 500,
            },
        )
