from typing import Optional, List, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from datetime import datetime
import logging

from auth import get_current_user
from models import (
    ProposalCreate,
    ProposalResponse,
    ProposalDetail,
    ProposalListResponse,
    ProposalStatusUpdate,
    ProposalStatusUpdateResponse,
    ProposalSubmitResponse,
    ProposalEvaluateResponse,
    DuplicateCheckResponse,
    CommentCreate,
    CommentResponse,
    BatchEvaluateRequest,
    BatchJobResponse,
    ExportResponse,
    ErrorResponse,
)
from services import (
    proposal_service,
    submit_service,
    status_service,
    evaluate_service,
    duplicate_check_service,
    comment_service,
)
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post(
    "",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - vendor authentication required"},
        403: {"model": ErrorResponse, "description": "Forbidden - only vendors can submit proposals"},
        422: {"model": ErrorResponse, "description": "Validation error - invalid sector or technology type"},
    },
)
async def create_proposal(
    payload: ProposalCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit new proposal with documents (vendor-only).
    Creates proposal record and returns pre-signed upload URLs for documents.
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        if user_role != "vendor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only vendors can submit proposals", "code": "VENDOR_ONLY"},
            )

        result = proposal_service.create_proposal(
            user_id=user_id,
            title=payload.title.strip(),
            sector=payload.sector,
            technology_type=payload.technology_type,
            maturity_level=payload.maturity_level,
            language=payload.language,
            business_group_id=payload.business_group_id,
            description=payload.description.strip() if payload.description else None,
            sourcing_case_id=payload.sourcing_case_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "InternalError", "detail": "Failed to create proposal", "code": "PROPOSAL_CREATE_FAILED"},
            )

        return ProposalResponse(
            proposal_id=UUID(result["id"]),
            status=result["status"],
            upload_urls=result.get("upload_urls", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating proposal: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/{proposal_id}/submit",
    response_model=ProposalSubmitResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        400: {"model": ErrorResponse, "description": "Cannot submit proposal without documents"},
    },
)
async def submit_proposal(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Finalize proposal submission and trigger AI evaluation queue.
    Validates that proposal has at least one document attached.
    """
    try:
        user_id = UUID(current_user["id"])

        result = submit_service.submit_proposal(
            user_id=user_id,
            proposal_id=proposal_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "BadRequest", "detail": "Cannot submit proposal without documents", "code": "NO_DOCUMENTS"},
            )

        return ProposalSubmitResponse(
            proposal_id=UUID(result["proposal_id"]),
            status=result["status"],
            estimated_completion=result["estimated_completion"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting proposal: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def list_proposals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user),
):
    """
    List proposals with filtering and pagination.
    Vendors see only their own proposals.
    Analysts and above see all proposals (filtered by chamber affiliation via RLS).
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        result = proposal_service.list_proposals(
            user_id=user_id,
            user_role=user_role,
            page=page,
            page_size=page_size,
            status=status_filter.strip() if status_filter else None,
            sector=sector.strip() if sector else None,
        )

        if not result:
            return {"proposals": [], "pagination": {"total": 0, "page": page, "page_size": page_size, "total_pages": 0}}

        return {
            "proposals": result.get("proposals", []),
            "pagination": result.get("pagination", {"total": 0, "page": page, "page_size": page_size, "total_pages": 0}),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ENDPOINT ERROR: {traceback.format_exc()}")
        logger.error(f"Error listing proposals: {str(e)}", exc_info=True)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get(
    "/{proposal_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions to view this proposal"},
    },
)
async def get_proposal_detail(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed proposal information including evaluation results.
    Access control:
    - Vendors: own proposals only
    - Business Group Leads: proposals in their sector
    - Analysts/Compliance Officers/Executives: all proposals
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        result = proposal_service.get_proposal_by_id(
            user_id=user_id,
            user_role=user_role,
            proposal_id=proposal_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": "PROPOSAL_NOT_FOUND"},
            )

        return ProposalDetail(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving proposal detail: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.patch(
    "/{proposal_id}/status",
    response_model=ProposalStatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only analysts and executives can update status"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        422: {"model": ErrorResponse, "description": "Invalid status transition"},
    },
)
async def update_proposal_status(
    proposal_id: UUID,
    payload: ProposalStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update proposal status (analyst/executive only).
    Valid transitions:
    - evaluated -> under_review
    - under_review -> approved/rejected
    - any -> requires_manual_review
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        if user_role not in ["analyst", "executive", "business_group_lead"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only analysts and executives can update status", "code": "INSUFFICIENT_PERMISSIONS"},
            )

        result = status_service.update_proposal_status(
            user_id=user_id,
            proposal_id=proposal_id,
            status=payload.status,
            reason=payload.reason.strip() if payload.reason else None,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or invalid status transition", "code": "INVALID_STATUS_TRANSITION"},
            )

        return ProposalStatusUpdateResponse(
            proposal_id=UUID(result["proposal_id"]),
            status=result["status"],
            updated_at=result["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating proposal status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/{proposal_id}/evaluate",
    response_model=ProposalEvaluateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only analysts can trigger re-evaluation"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        409: {"model": ErrorResponse, "description": "Proposal is already being evaluated"},
    },
)
async def trigger_evaluation(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger manual re-evaluation of proposal (analyst only).
    Queues proposal for AI evaluation job.
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        if user_role not in ["analyst", "business_group_lead"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only analysts can trigger re-evaluation", "code": "ANALYST_ONLY"},
            )

        result = evaluate_service.trigger_proposal_evaluation(
            user_id=user_id,
            proposal_id=proposal_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "detail": "Proposal is already being evaluated", "code": "ALREADY_EVALUATING"},
            )

        return ProposalEvaluateResponse(
            proposal_id=UUID(result["proposal_id"]),
            status=result["status"],
            job_id=UUID(result["job_id"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering evaluation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/{proposal_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        422: {"model": ErrorResponse, "description": "Comment text too long"},
    },
)
async def add_comment(
    proposal_id: UUID,
    payload: CommentCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Add comment to proposal.
    Comments can be internal (default) or vendor_visible.
    """
    try:
        user_id = UUID(current_user["id"])

        if len(payload.comment_text.strip()) > 2000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "ValidationError", "detail": "Comment text exceeds 2000 characters", "code": "COMMENT_TOO_LONG"},
            )

        result = comment_service.create_comment(
            user_id=user_id,
            proposal_id=proposal_id,
            comment_text=payload.comment_text.strip(),
            visibility=payload.visibility,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": "PROPOSAL_NOT_FOUND"},
            )

        return CommentResponse(
            comment_id=UUID(result["comment_id"]),
            proposal_id=UUID(result["proposal_id"]),
            user_id=UUID(result["user_id"]),
            comment_text=result["comment_text"],
            created_at=result["created_at"],
            visibility=result["visibility"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/{proposal_id}/duplicate-check",
    response_model=DuplicateCheckResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
    },
)
async def run_duplicate_check(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Run semantic similarity check against existing proposals.
    Uses Claude embeddings to detect near-duplicate submissions.
    """
    try:
        user_id = UUID(current_user["id"])

        result = await duplicate_check_service.run_duplicate_check(
            user_id=str(user_id),
            proposal_id=proposal_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found or access denied", "code": "PROPOSAL_NOT_FOUND"},
            )

        return DuplicateCheckResponse(
            proposal_id=UUID(result["proposal_id"]),
            is_duplicate=result["is_duplicate"],
            similar_proposals=result["similar_proposals"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running duplicate check: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/{proposal_id}/request-revision",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - vendor role required or not owner"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        409: {"model": ErrorResponse, "description": "Proposal not in an evaluable state"},
    },
)
async def request_revision(
    proposal_id: UUID,
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """Vendor requests revision on their evaluated proposal."""
    try:
        user_id = str(current_user["id"])
        user_role = current_user.get("role", "").strip()

        if user_role not in ("vendor", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only vendors can request revisions", "code": "VENDOR_ONLY"},
            )

        proposal_response = supabase.table("chamber_proposals").select(
            "id, submitter_id, status"
        ).eq("id", str(proposal_id)).single().execute()

        if not proposal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "Proposal not found", "code": "PROPOSAL_NOT_FOUND"},
            )

        proposal = proposal_response.data

        if user_role == "vendor" and str(proposal["submitter_id"]) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Access denied to this proposal", "code": "ACCESS_DENIED"},
            )

        if proposal["status"] not in ("evaluated", "needs_improvement", "under_review", "shortlisted"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "detail": f"Cannot request revision on proposal with status '{proposal['status']}'", "code": "INVALID_STATUS"},
            )

        # Update proposal status
        supabase.table("chamber_proposals").update({
            "status": "revision_requested",
        }).eq("id", str(proposal_id)).execute()

        # Add comment with vendor's notes
        notes = payload.get("notes", "").strip() if isinstance(payload, dict) else ""
        comment_text = f"Vendor requested revision{': ' + notes if notes else ''}"

        user_check = supabase.table("chamber_users").select("id").eq("id", user_id).maybe_single().execute()
        if user_check.data:
            supabase.table("chamber_comments").insert({
                "proposal_id": str(proposal_id),
                "user_id": user_id,
                "comment_text": comment_text,
                "visibility": "vendor_visible",
            }).execute()

        return {
            "proposal_id": str(proposal_id),
            "status": "revision_requested",
            "message": "Revision requested successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting revision: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/batch/evaluate",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst role required"},
        422: {"model": ErrorResponse, "description": "Batch size exceeds limit of 100"},
    },
)
async def batch_evaluate_proposals(
    payload: BatchEvaluateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger batch evaluation for multiple proposals (analyst only).
    Max 100 proposals per batch.
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        if user_role not in ["analyst", "executive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Analyst role required", "code": "ANALYST_ONLY"},
            )

        if len(payload.proposal_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "ValidationError", "detail": "Batch size exceeds limit of 100", "code": "BATCH_TOO_LARGE"},
            )

        result = evaluate_service.batch_evaluate_proposals(
            user_id=user_id,
            proposal_ids=payload.proposal_ids,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "InternalError", "detail": "Failed to queue batch evaluation", "code": "BATCH_QUEUE_FAILED"},
            )

        return BatchJobResponse(
            batch_job_id=UUID(result["batch_job_id"]),
            proposal_count=result["proposal_count"],
            status=result["status"],
            estimated_completion=result["estimated_completion"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queuing batch evaluation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst or executive role required"},
    },
)
async def export_proposals(
    format: Literal["csv", "xlsx"] = Query("csv", description="Export format"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user),
):
    """
    Export proposals data as CSV/Excel (analyst/executive only).
    Returns temporary download URL with expiration.
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "").strip()

        if user_role not in ["analyst", "executive", "compliance_officer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Analyst or executive role required", "code": "INSUFFICIENT_PERMISSIONS"},
            )

        result = proposal_service.export_proposals(
            user_id=user_id,
            export_format=format,
            sector=sector.strip() if sector else None,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "InternalError", "detail": "Failed to generate export", "code": "EXPORT_FAILED"},
            )

        return ExportResponse(
            export_url=result["export_url"],
            expires_at=result["expires_at"],
            format=format,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting proposals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
        )
