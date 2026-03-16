"""Proposal submission and AI evaluation routes."""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import logging

from auth import get_current_user
from database import supabase
from services.evaluation_engine import EvaluationEngine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Proposal Submission & AI Evaluation"])

evaluation_engine = EvaluationEngine()


# --- Request/Response Models ---

class ProposalSubmitRequest(BaseModel):
    title: str = Field(..., max_length=255, description="Proposal title")
    sector: str = Field(..., description="Sector / business group keyword")
    technology_type: str = Field(..., description="Technology type (e.g. Machine Learning)")
    maturity_level: str = Field(
        ...,
        pattern="^(concept|prototype|mvp|production|scaled)$",
        description="Maturity level",
    )
    language: str = Field(
        default="en",
        pattern="^(en|ar|mixed)$",
        description="Proposal language",
    )
    description: Optional[str] = Field(None, description="Detailed proposal description")


class ProposalStatusPatch(BaseModel):
    status: str = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")


# --- POST /api/v1/proposals (create) ---

@router.post(
    "/proposals",
    status_code=status.HTTP_201_CREATED,
)
async def create_proposal(
    payload: ProposalSubmitRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new proposal. Any authenticated role."""
    try:
        user_id = current_user["id"]
        user_email = current_user.get("email", "")

        # Ensure vendor record exists (submitter_id FK -> chamber_vendors)
        vendor_check = (
            supabase.table("chamber_vendors")
            .select("id")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )
        if not vendor_check.data:
            vendor_data = {
                "id": str(user_id),
                "name": user_email.split("@")[0] if user_email else "unknown",
                "country": "UAE",
                "contact_email": user_email,
                "is_desc_approved": False,
                "onboarding_status": "submitted",
                "submission_history_count": 0,
            }
            supabase.table("chamber_vendors").insert(vendor_data).execute()
            logger.info(f"Auto-created vendor record for user {user_id}")

        # Auto-assign business_group_id by matching sector keyword
        business_group_id = None
        try:
            bg_result = (
                supabase.table("chamber_business_groups")
                .select("id, name")
                .execute()
            )
            if bg_result.data:
                sector_lower = payload.sector.lower()
                for bg in bg_result.data:
                    if sector_lower in bg["name"].lower():
                        business_group_id = bg["id"]
                        break
        except Exception as bg_err:
            logger.warning(f"Business group lookup failed: {bg_err}")

        proposal_data = {
            "title": payload.title.strip(),
            "sector": payload.sector.strip(),
            "technology_type": payload.technology_type.strip(),
            "maturity_level": payload.maturity_level,
            "language": payload.language,
            "description": payload.description.strip() if payload.description else None,
            "submitter_id": str(user_id),
            "status": "queued",
            "submission_date": datetime.now(timezone.utc).isoformat(),
            "is_duplicate": False,
            "requires_manual_review": False,
        }
        if business_group_id:
            proposal_data["business_group_id"] = str(business_group_id)

        result = supabase.table("chamber_proposals").insert(proposal_data).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to create proposal", "code": 500},
            )

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )


# --- GET /api/v1/proposals (list) ---

@router.get(
    "/proposals",
    status_code=status.HTTP_200_OK,
)
async def list_proposals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    sector: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List proposals with optional status filter."""
    try:
        offset = (page - 1) * page_size

        query = supabase.table("chamber_proposals").select(
            "id, title, submitter_id, submission_date, status, sector, technology_type, maturity_level, language, composite_score, relevance_score, feasibility_score, sector_alignment_score, compliance_score, is_duplicate, requires_manual_review, business_group_id, description",
            count="exact",
        )

        # Role-based filtering
        user_role = current_user.get("role", "vendor")
        if user_role == "vendor":
            query = query.eq("submitter_id", str(current_user["id"]))

        if status_filter:
            query = query.eq("status", status_filter)
        if sector:
            query = query.eq("sector", sector)

        query = query.order("submission_date", desc=True).range(offset, offset + page_size - 1)
        result = query.execute()

        total = result.count if result.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "proposals": result.data or [],
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }
    except Exception as e:
        logger.error(f"Error listing proposals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )


# --- GET /api/v1/proposals/{id} (detail with evaluation) ---

@router.get(
    "/proposals/{proposal_id}",
    status_code=status.HTTP_200_OK,
)
async def get_proposal_detail(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get single proposal with its evaluation if exists."""
    try:
        proposal_result = (
            supabase.table("chamber_proposals")
            .select("*")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )

        if not proposal_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Proposal not found", "code": 404},
            )

        proposal = proposal_result.data

        # Fetch evaluation if exists
        eval_result = (
            supabase.table("chamber_evaluations")
            .select("*")
            .eq("proposal_id", str(proposal_id))
            .order("evaluated_at", desc=True)
            .limit(1)
            .execute()
        )
        evaluation = eval_result.data[0] if eval_result.data else None

        # Fetch AI interaction cost data if evaluation exists
        ai_cost = None
        if evaluation:
            ai_result = (
                supabase.table("chamber_ai_interactions")
                .select("prompt_tokens, completion_tokens, latency_ms, cost_usd, energy_kwh, carbon_gco2, intelligence_units")
                .eq("evaluation_id", str(evaluation["id"]))
                .limit(1)
                .execute()
            )
            if ai_result.data:
                ai_cost = ai_result.data[0]

        # Fetch business group info
        business_group = None
        if proposal.get("business_group_id"):
            bg_result = (
                supabase.table("chamber_business_groups")
                .select("id, name, chamber, description")
                .eq("id", str(proposal["business_group_id"]))
                .maybe_single()
                .execute()
            )
            business_group = bg_result.data

        return {
            **proposal,
            "evaluation": evaluation,
            "ai_cost": ai_cost,
            "business_group": business_group,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting proposal detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )


# --- PATCH /api/v1/proposals/{id}/status ---

@router.patch(
    "/proposals/{proposal_id}/status",
    status_code=status.HTTP_200_OK,
)
async def update_proposal_status(
    proposal_id: UUID,
    payload: ProposalStatusPatch,
    current_user: dict = Depends(get_current_user),
):
    """Update proposal status (admin/analyst only)."""
    allowed_roles = ["admin", "analyst"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Forbidden", "detail": "Admin or analyst role required", "code": 403},
        )

    try:
        # Check proposal exists
        existing = (
            supabase.table("chamber_proposals")
            .select("id, status")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Proposal not found", "code": 404},
            )

        update_data = {
            "status": payload.status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("chamber_proposals")
            .update(update_data)
            .eq("id", str(proposal_id))
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Failed to update status", "code": 500},
            )

        return {
            "proposal_id": str(proposal_id),
            "status": payload.status,
            "updated_at": update_data["updated_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating proposal status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )


# --- POST /api/v1/proposals/{id}/evaluate ---

@router.post(
    "/proposals/{proposal_id}/evaluate",
    status_code=status.HTTP_200_OK,
)
async def trigger_ai_evaluation(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Trigger AI evaluation for a proposal. Admin or analyst only."""
    allowed_roles = ["admin", "analyst"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Forbidden", "detail": "Admin or analyst role required", "code": 403},
        )

    try:
        # Validate proposal exists and status allows evaluation
        proposal_result = (
            supabase.table("chamber_proposals")
            .select("id, status, title")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )

        if not proposal_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Proposal not found", "code": 404},
            )

        current_status = proposal_result.data["status"]
        if current_status not in ("queued", "submitted", "requires_manual_review", "requires_review"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid status",
                    "detail": f"Cannot evaluate proposal with status '{current_status}'. Must be 'queued', 'submitted', 'requires_manual_review', or 'requires_review'.",
                    "code": 400,
                },
            )

        # Set status to evaluating immediately
        supabase.table("chamber_proposals").update({
            "status": "evaluating",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", str(proposal_id)).execute()

        # Run evaluation
        result = await evaluation_engine.evaluate_proposal(
            proposal_id=str(proposal_id),
            user_id=str(current_user["id"]),
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Revert status on failure
        try:
            supabase.table("chamber_proposals").update({
                "status": "queued",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", str(proposal_id)).execute()
        except Exception:
            pass
        logger.error(f"Error evaluating proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Evaluation failed", "detail": str(e), "code": 500},
        )


# --- GET /api/v1/evaluations (list) ---

@router.get(
    "/evaluations",
    status_code=status.HTTP_200_OK,
)
async def list_evaluations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List all evaluations joined with proposal title."""
    try:
        offset = (page - 1) * page_size

        eval_result = (
            supabase.table("chamber_evaluations")
            .select("*", count="exact")
            .order("evaluated_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        evaluations = eval_result.data or []
        total = eval_result.count if eval_result.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # Enrich with proposal titles
        for ev in evaluations:
            if ev.get("proposal_id"):
                p_result = (
                    supabase.table("chamber_proposals")
                    .select("title, sector, status")
                    .eq("id", str(ev["proposal_id"]))
                    .maybe_single()
                    .execute()
                )
                if p_result.data:
                    ev["proposal_title"] = p_result.data["title"]
                    ev["proposal_sector"] = p_result.data["sector"]
                    ev["proposal_status"] = p_result.data["status"]

        return {
            "evaluations": evaluations,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }
    except Exception as e:
        logger.error(f"Error listing evaluations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )


# --- GET /api/v1/evaluations/{id} (detail) ---

@router.get(
    "/evaluations/{evaluation_id}",
    status_code=status.HTTP_200_OK,
)
async def get_evaluation_detail(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get evaluation detail with full reasoning."""
    try:
        result = (
            supabase.table("chamber_evaluations")
            .select("*")
            .eq("id", str(evaluation_id))
            .maybe_single()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Evaluation not found", "code": 404},
            )

        evaluation = result.data

        # Enrich with proposal info
        if evaluation.get("proposal_id"):
            p_result = (
                supabase.table("chamber_proposals")
                .select("title, sector, technology_type, maturity_level, status")
                .eq("id", str(evaluation["proposal_id"]))
                .maybe_single()
                .execute()
            )
            if p_result.data:
                evaluation["proposal"] = p_result.data

        # Fetch AI cost data
        ai_result = (
            supabase.table("chamber_ai_interactions")
            .select("prompt_tokens, completion_tokens, latency_ms, cost_usd, energy_kwh, carbon_gco2, intelligence_units")
            .eq("evaluation_id", str(evaluation_id))
            .limit(1)
            .execute()
        )
        evaluation["ai_cost"] = ai_result.data[0] if ai_result.data else None

        return evaluation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )
