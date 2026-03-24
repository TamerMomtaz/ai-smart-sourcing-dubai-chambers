from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime, timezone

from auth import get_current_user
from models.auth import UserInfo
from models.proposal import (
    ProposalCreate,
    ProposalResponse,
    ProposalDetail,
    ProposalListResponse,
    ProposalStatusUpdate,
    ProposalStatusUpdateResponse,
    ProposalSubmitResponse,
    ProposalEvaluateResponse,
    DuplicateCheckResponse,
)
from models.common import ErrorResponse, PaginationResponse
from services.chamber_proposal_service import ChamberProposalService
from services.proposal_service import create_proposal
from services.submit_service import submit_proposal
from services.evaluate_service import trigger_proposal_evaluation
from services.status_service import update_proposal_status
from services.duplicate_check_service import run_duplicate_check
from database import supabase

router = APIRouter(prefix="/chamber_proposals", tags=["chamber_proposals"])


@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Proposal created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - vendor role required"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_chamber_proposal(
    payload: ProposalCreate,
    current_user: UserInfo = Depends(get_current_user),
):
    """Create a new chamber proposal (vendor-only operation)."""
    try:
        if current_user.role != "vendor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only vendors can create proposals", "code": 403},
            )

        result = create_proposal(
            user_id=current_user.id,
            title=payload.title,
            sector=payload.sector,
            technology_type=payload.technology_type,
            maturity_level=payload.maturity_level,
            language=payload.language,
            business_group_id=payload.business_group_id,
            description=payload.description,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "InternalServerError", "detail": "Failed to create proposal", "code": 500},
            )

        return ProposalResponse(
            proposal_id=result["id"],
            status=result["status"],
            upload_urls=result.get("upload_urls", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Proposals retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_chamber_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by proposal status"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: UserInfo = Depends(get_current_user),
):
    """List chamber proposals with pagination and filters."""
    try:
        offset = (page - 1) * page_size

        query = supabase.table("chamber_proposals").select(
            "id, title, submitter_id, submission_date, status, sector, technology_type, maturity_level, composite_score, is_duplicate, requires_manual_review",
            count="exact",
        )

        if current_user.role == "vendor":
            query = query.eq("submitter_id", str(current_user.id))
        elif current_user.role == "business_group_lead":
            user_bg = supabase.table("chamber_users").select("business_group_id").eq("id", str(current_user.id)).single().execute()
            if user_bg.data and user_bg.data.get("business_group_id"):
                query = query.eq("business_group_id", user_bg.data["business_group_id"])

        if status_filter:
            query = query.eq("status", status_filter)
        if sector:
            query = query.eq("sector", sector)

        query = query.order("submission_date", desc=True).range(offset, offset + page_size - 1)

        response = query.execute()

        if not response.data:
            return {
                "proposals": [],
                "pagination": {"total": 0, "page": page, "page_size": page_size, "total_pages": 0},
            }

        total = response.count if response.count else 0
        total_pages = (total + page_size - 1) // page_size

        # Enrich proposals with vendor DESC certification status
        proposals = response.data
        submitter_ids = list({str(p["submitter_id"]) for p in proposals if p.get("submitter_id")})
        vendor_desc_map = {}
        if submitter_ids:
            vendor_query = supabase.table("chamber_vendors").select(
                "id, is_desc_approved, desc_certified_provider_id"
            ).in_("id", submitter_ids).execute()
            for v in (vendor_query.data or []):
                vendor_desc_map[v["id"]] = {
                    "vendor_desc_certified": bool(v.get("desc_certified_provider_id")) or v.get("is_desc_approved", False),
                }

        for p in proposals:
            vendor_info = vendor_desc_map.get(str(p.get("submitter_id")), {})
            p["vendor_desc_certified"] = vendor_info.get("vendor_desc_certified", False)

        return {
            "proposals": proposals,
            "pagination": {"total": total, "page": page, "page_size": page_size, "total_pages": total_pages},
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ENDPOINT ERROR: {traceback.format_exc()}")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get(
    "/{proposal_id}",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Proposal detail retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - access denied"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_chamber_proposal_by_id(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Get chamber proposal by ID with full details."""
    try:
        proposal_response = supabase.table("chamber_proposals").select(
            "id, title, submitter_id, submission_date, status, sector, technology_type, maturity_level, language, composite_score, relevance_score, feasibility_score, sector_alignment_score, compliance_score, evaluation_timestamp, is_duplicate, requires_manual_review, d33_alignment_metrics, business_group_id"
        ).eq("id", str(proposal_id)).single().execute()

        if not proposal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found", "code": 404},
            )

        proposal = proposal_response.data

        if current_user.role == "vendor" and str(proposal["submitter_id"]) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Access denied to this proposal", "code": 403},
            )

        if current_user.role == "business_group_lead":
            user_bg = supabase.table("chamber_users").select("business_group_id").eq("id", str(current_user.id)).single().execute()
            if user_bg.data and str(user_bg.data.get("business_group_id")) != str(proposal.get("business_group_id")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "Forbidden", "detail": "Access denied to this business group", "code": 403},
                )

        vendor_response = supabase.table("chamber_vendors").select(
            "id, name, company_registration, is_desc_approved"
        ).eq("id", str(proposal["submitter_id"])).single().execute()

        vendor = vendor_response.data if vendor_response.data else {}

        documents_response = supabase.table("chamber_documents").select(
            "id, file_name, file_type, file_size, uploaded_at"
        ).eq("proposal_id", str(proposal_id)).execute()

        documents = documents_response.data if documents_response.data else []

        evaluation = None
        evaluation_response = supabase.table("chamber_evaluations").select(
            "relevance_reasoning, feasibility_reasoning, sector_reasoning, compliance_reasoning, summary_en, summary_ar, hallucination_check_passed, prompt_injection_detected"
        ).eq("proposal_id", str(proposal_id)).order("evaluated_at", desc=True).limit(1).execute()

        if evaluation_response.data:
            evaluation = evaluation_response.data[0]

        audits_response = supabase.table("chamber_compliance_audits").select(
            "id, audit_type, isr_v3_compliance, ai_security_policy_compliance, csp_standards_compliance, data_residency_verified, audit_timestamp, remediation_required"
        ).eq("proposal_id", str(proposal_id)).order("audit_timestamp", desc=True).execute()

        audits = audits_response.data if audits_response.data else []

        comments_query = supabase.table("chamber_comments").select(
            "id, user_id, comment_text, created_at, visibility"
        ).eq("proposal_id", str(proposal_id)).order("created_at", desc=True)

        if current_user.role == "vendor":
            comments_query = comments_query.eq("visibility", "vendor_visible")

        comments_response = comments_query.execute()
        comments = comments_response.data if comments_response.data else []

        for comment in comments:
            user_response = supabase.table("chamber_users").select("full_name").eq("id", str(comment["user_id"])).single().execute()
            comment["user_name"] = user_response.data["full_name"] if user_response.data else "Unknown"

        return ProposalDetail(
            id=proposal["id"],
            title=proposal["title"],
            submitter_id=proposal["submitter_id"],
            vendor=vendor,
            submission_date=proposal["submission_date"],
            status=proposal["status"],
            sector=proposal["sector"],
            technology_type=proposal["technology_type"],
            maturity_level=proposal["maturity_level"],
            language=proposal["language"],
            composite_score=proposal.get("composite_score"),
            relevance_score=proposal.get("relevance_score"),
            feasibility_score=proposal.get("feasibility_score"),
            sector_alignment_score=proposal.get("sector_alignment_score"),
            compliance_score=proposal.get("compliance_score"),
            evaluation_timestamp=proposal.get("evaluation_timestamp"),
            is_duplicate=proposal["is_duplicate"],
            requires_manual_review=proposal["requires_manual_review"],
            d33_alignment_metrics=proposal.get("d33_alignment_metrics"),
            documents=documents,
            evaluation=evaluation,
            compliance_audits=audits,
            comments=comments,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )


@router.put(
    "/{proposal_id}/status",
    response_model=ProposalStatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Proposal status updated successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst or executive role required"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_chamber_proposal_status(
    proposal_id: UUID,
    payload: ProposalStatusUpdate,
    current_user: UserInfo = Depends(get_current_user),
):
    """Update proposal status (analyst/executive only)."""
    try:
        if current_user.role not in ["analyst", "executive", "business_group_lead"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Insufficient permissions to update proposal status", "code": 403},
            )

        result = update_proposal_status(
            user_id=current_user.id,
            proposal_id=proposal_id,
            status=payload.status,
            reason=payload.reason,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": 404},
            )

        return ProposalStatusUpdateResponse(
            proposal_id=result["proposal_id"],
            status=result["status"],
            updated_at=result["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )


@router.post(
    "/{proposal_id}/submit",
    response_model=ProposalSubmitResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Proposal submitted for evaluation"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - vendor role required"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def submit_chamber_proposal(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Submit proposal for evaluation (vendor-only operation)."""
    try:
        if current_user.role != "vendor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only vendors can submit proposals", "code": 403},
            )

        result = submit_proposal(user_id=current_user.id, proposal_id=proposal_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": 404},
            )

        return ProposalSubmitResponse(
            proposal_id=result["proposal_id"],
            status=result["status"],
            estimated_completion=result["estimated_completion"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )


@router.post(
    "/{proposal_id}/evaluate",
    response_model=ProposalEvaluateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Evaluation triggered successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst role required"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def evaluate_chamber_proposal(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Trigger manual re-evaluation of a proposal (analyst only)."""
    try:
        if current_user.role not in ["analyst", "business_group_lead"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Insufficient permissions to trigger evaluation", "code": 403},
            )

        result = trigger_proposal_evaluation(user_id=current_user.id, proposal_id=proposal_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": 404},
            )

        return ProposalEvaluateResponse(
            proposal_id=result["proposal_id"],
            status=result["status"],
            job_id=result["job_id"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )


@router.post(
    "/{proposal_id}/duplicate-check",
    response_model=DuplicateCheckResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Duplicate check completed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def check_duplicate_chamber_proposal(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Run duplicate check against existing proposals."""
    try:
        result = await run_duplicate_check(user_id=str(current_user.id), proposal_id=proposal_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": 404},
            )

        return DuplicateCheckResponse(
            proposal_id=result["proposal_id"],
            is_duplicate=result["is_duplicate"],
            similar_proposals=result.get("similar_proposals", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )


@router.delete(
    "/{proposal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Proposal deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - admin role required"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_chamber_proposal(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Delete proposal (admin-only operation, soft delete via RLS)."""
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Admin role required to delete proposals", "code": 403},
            )

        proposal_response = supabase.table("chamber_proposals").select("id").eq("id", str(proposal_id)).single().execute()

        if not proposal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found", "code": 404},
            )

        delete_response = supabase.table("chamber_proposals").delete().eq("id", str(proposal_id)).execute()

        if not delete_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "InternalServerError", "detail": "Failed to delete proposal", "code": 500},
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": str(e), "code": 500},
        )
